"""Oracle strength of changed JUnit tests: does each test assert a value or an exception?

Evidence: 2606.18168 (most agent-authored test patches carry weak or no
assertions; strong multi-type oracles correlate with merge), 2608.16742 /
2608.19799 (self-consistent wrong tests, public-pass/hidden-fail).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from quality_router.harness.coverage_gate import is_test_path
from quality_router.harness.javasrc import TestMethod, test_methods
from quality_router.harness.report import GateResult

STRONG_CALLS = (
    "assertEquals", "assertNotEquals", "assertArrayEquals", "assertIterableEquals",
    "assertLinesMatch", "assertSame", "assertNotSame", "assertThrows", "assertThrowsExactly",
    "assertInstanceOf", "assertThatThrownBy", "assertThatExceptionOfType",
    "assertThatIllegalArgumentException", "assertThatIllegalStateException",
    "assertThatNullPointerException", "assertThatIOException", "assertJsonEquals",
    "assertEqualsIgnoringCase",
)
WEAK_CALLS = ("assertNotNull", "assertNull", "assertTrue", "assertFalse", "assertDoesNotThrow")
ASSERTJ_STRONG = (
    "isEqualTo", "isNotEqualTo", "isEqualByComparingTo", "isEqualToComparingFieldByField",
    "containsExactly", "containsExactlyInAnyOrder", "containsOnly", "containsEntry",
    "containsKey", "contains", "doesNotContain", "hasSize", "hasSizeGreaterThan", "isEmpty",
    "isGreaterThan", "isGreaterThanOrEqualTo", "isLessThan", "isLessThanOrEqualTo", "isBetween",
    "isCloseTo", "startsWith", "endsWith", "matches", "hasMessage", "hasMessageContaining",
    "isInstanceOf", "hasFieldOrPropertyWithValue", "usingRecursiveComparison", "extracting",
    "satisfies", "allSatisfy", "anySatisfy", "isSameAs", "isIn", "isNotIn", "hasValue",
    "isPresent", "isEmptyOptional", "hasCauseInstanceOf", "isSorted", "hasToString",
)
HAMCREST_STRONG = ("equalTo", "is(", "contains(", "containsInAnyOrder", "hasItem", "hasSize",
                   "hasEntry", "closeTo", "greaterThan", "lessThan", "instanceOf", "sameInstance",
                   "hasProperty", "containsString", "startsWith", "endsWith", "empty(")

_CALL = re.compile(r"\b(\w+)\s*\(")
_ASSERT_THAT = re.compile(r"\bassertThat\s*\(")
_VERIFY = re.compile(r"\bverify\s*\(")
_CUSTOM_ASSERT = re.compile(r"\b(assert[A-Z]\w*|verify[A-Z]\w*|expect[A-Z]\w*)\s*\(")


@dataclass(frozen=True)
class OracleVerdict:
    strong: int
    weak: int
    mocks: int
    custom: int

    @property
    def kind(self) -> str:
        if self.strong or self.custom:
            return "strong"
        if self.weak:
            return "weak"
        if self.mocks:
            return "mock_only"
        return "none"


def classify(method: TestMethod, helpers: tuple[str, ...] = ()) -> OracleVerdict:
    body = method.body
    names = [m.group(1) for m in _CALL.finditer(body)]
    strong = sum(1 for n in names if n in STRONG_CALLS)
    weak = sum(1 for n in names if n in WEAK_CALLS)
    strong += sum(1 for n in names if n in helpers)
    if re.search(r"\bexpected\s*=", method.annotation_args):
        strong += 1
    if re.search(r"\bfail\s*\(", body) and re.search(r"\bcatch\s*\(", body):
        strong += 1
    for match in _ASSERT_THAT.finditer(body):
        close = _matching_paren(body, match.end() - 1)
        args = body[match.end():close]
        statement_end = body.find(";", close)
        tail = body[close + 1:statement_end if statement_end >= 0 else len(body)]
        chain = re.findall(r"\.\s*(\w+)\s*\(", tail)
        hamcrest = "," in args and any(re.search(r"\b" + re.escape(h), args)
                                       for h in HAMCREST_STRONG)
        if any(c in ASSERTJ_STRONG for c in chain) or hamcrest:
            strong += 1
        else:
            weak += 1
    mocks = len(_VERIFY.findall(body))
    known = set(STRONG_CALLS) | set(WEAK_CALLS) | set(helpers)
    custom = sum(1 for m in _CUSTOM_ASSERT.finditer(body) if m.group(1) not in known
                 and not m.group(1).startswith("assertThat"))
    return OracleVerdict(strong=strong, weak=weak, mocks=mocks, custom=custom)


def _matching_paren(text: str, open_index: int) -> int:
    depth = 0
    for i in range(open_index, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return len(text) - 1


def run_test_oracles(
    files: dict[str, set[int] | None],
    cwd: Path,
    allow_weak: bool = False,
    helpers: tuple[str, ...] = (),
) -> GateResult:
    """files: path -> changed lines (None = check every test method in the file)."""
    result = GateResult(gate="test-oracles")
    counts = {"strong": 0, "weak": 0, "mock_only": 0, "none": 0}
    for path in sorted(files):
        if not path.endswith(".java"):
            continue
        source_path = cwd / path
        if not source_path.is_file():
            continue
        changed = files[path]
        if changed is not None and not is_test_path(path):
            continue
        for method in test_methods(source_path.read_text(encoding="utf-8")):
            span = set(range(method.start_line, method.end_line + 1))
            if changed is not None and not (span & changed):
                continue
            verdict = classify(method, helpers)
            counts[verdict.kind] += 1
            if verdict.kind == "strong":
                if verdict.custom and not verdict.strong:
                    result.add("info", "custom_assertion",
                               f"{method.name}: relies on a custom assert*/verify* helper",
                               path, method.start_line)
                continue
            message = {
                "weak": "only null/boolean/no-throw assertions; assert an expected value "
                        "or exception",
                "mock_only": "only Mockito verify(); no assertion on output or state",
                "none": "no assertion at all",
            }[verdict.kind]
            level = "warning" if allow_weak and verdict.kind == "weak" else "error"
            result.add(level, f"{verdict.kind}_oracle", f"{method.name}: {message}",
                       path, method.start_line)
    result.summary.update({f"tests_{k}": v for k, v in counts.items()})
    result.summary["tests_checked"] = sum(counts.values())
    return result
