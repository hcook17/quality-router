"""Oracle strength of changed JUnit tests: does each test assert a value or an exception?

Evidence: 2606.18168 (most agent-authored test patches carry weak or no
assertions; strong multi-type oracles correlate with merge), 2608.16742 /
2608.19799 (self-consistent wrong tests, public-pass/hidden-fail).

Spring Boot 2.7-4.x web and reactive tests are judged per chain: MockMvc
`andExpect`, WebTestClient / RestTestClient (Boot 4) `expect*` exchanges,
MockMvcTester (Boot 3.4+) AssertJ chains and Reactor StepVerifier. A status,
content-type or existence check alone is weak; asserting a body, value,
header value, view or redirect is strong.
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
    # Spring MockMvcTester (Boot 3.4+) and AssertJ JSON assertions.
    "hasBodyTextEqualTo", "isLenientlyEqualTo", "isStrictlyEqualTo", "hasViewName",
    "hasRedirectedUrl", "hasForwardedUrl", "hasHeader", "hasPathSatisfying", "hasFailed",
)
HAMCREST_STRONG = ("equalTo", "is(", "contains(", "containsInAnyOrder", "hasItem", "hasSize",
                   "hasEntry", "closeTo", "greaterThan", "lessThan", "instanceOf", "sameInstance",
                   "hasProperty", "containsString", "startsWith", "endsWith", "empty(")

_CALL = re.compile(r"\b(\w+)\s*\(")
_ASSERT_THAT = re.compile(r"\bassertThat\s*\(")
MOCKITO_VERIFY = ("verify", "verifyNoMoreInteractions", "verifyNoInteractions",
                  "verifyZeroInteractions")
_VERIFY = re.compile(r"\b(?:" + "|".join(MOCKITO_VERIFY) + r")\s*\(")
_CUSTOM_ASSERT = re.compile(r"\b(assert[A-Z]\w*|verify[A-Z]\w*|expect[A-Z]\w*)\s*\(")
_BDD_THEN_SHOULD = re.compile(r"\bthen\s*\([^;]*?\)\s*\.\s*should\w*\s*\(")

# Spring test idioms, judged per chain: a status/type/existence check alone is weak,
# a body, value, header value, view or redirect check is strong.
_MVC_EXPECT = re.compile(r"\.\s*andExpect(?:All)?\s*\(")
_MVC_STATUS = re.compile(r"\s*(?:\w+\s*\.\s*)*status\s*\(")
MVC_STRONG = ("value", "json", "string", "xml", "bytes", "attribute", "name", "redirectedUrl",
              "forwardedUrl", "redirectedUrlPattern", "forwardedUrlPattern", "equalTo", "is",
              "isEqualTo", "containsString", "hasSize", "hasItem", "contains",
              "containsInAnyOrder", "startsWith", "endsWith", "attributeHasFieldErrors",
              "attributeHasErrors", "dateValue", "longValue")
_EXCHANGE = re.compile(r"\.\s*(expectStatus|expectBody|expectBodyList|expectHeader|expectCookie)"
                       r"\s*\(")
EXCHANGE_STRONG = ("isEqualTo", "value", "valueEquals", "json", "xml", "consumeWith",
                   "hasSize", "contains", "containsExactly", "doesNotContain", "isEmpty",
                   "valueMatches", "isLenientlyEqualTo", "isStrictlyEqualTo", "isNotEqualTo")
_STEP_VERIFIER = re.compile(r"\bStepVerifier\s*\.\s*(?:create|withVirtualTime)\b"
                            r"|\bStepVerifier\s*::\s*create\b")
STEP_STRONG = ("expectNext", "expectNextMatches", "expectNextSequence", "expectNextCount",
               "assertNext", "consumeNextWith", "expectError", "expectErrorMessage",
               "expectErrorMatches", "expectErrorSatisfies", "verifyError",
               "verifyErrorMessage", "verifyErrorMatches", "verifyErrorSatisfies",
               "expectRecordedMatches", "consumeErrorWith")


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
    spring_strong, spring_weak, handled = _spring_oracles(body)
    strong += spring_strong
    weak += spring_weak
    mocks = len(_VERIFY.findall(body)) + len(_BDD_THEN_SHOULD.findall(body))
    known = set(STRONG_CALLS) | set(WEAK_CALLS) | set(helpers) | set(MOCKITO_VERIFY)
    custom = sum(1 for m in _CUSTOM_ASSERT.finditer(body) if m.group(1) not in known
                 and not m.group(1).startswith("assertThat")
                 and not any(s <= m.start() < e for s, e in handled))
    return OracleVerdict(strong=strong, weak=weak, mocks=mocks, custom=custom)


def _statements(body: str) -> list[tuple[int, int]]:
    """Spans of top-level statements; parenthesised lambdas stay inside their statement."""
    spans: list[tuple[int, int]] = []
    depth, start = 0, 0
    for i, ch in enumerate(body):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(depth - 1, 0)
        elif depth == 0 and ch in ";{}":
            spans.append((start, i))
            start = i + 1
    spans.append((start, len(body)))
    return [(s, e) for s, e in spans if body[s:e].strip()]


def _split_args(args: str) -> list[str]:
    parts: list[str] = []
    depth, start = 0, 0
    for i, ch in enumerate(args):
        if ch in "({":
            depth += 1
        elif ch in ")}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(args[start:i])
            start = i + 1
    parts.append(args[start:])
    return [p for p in parts if p.strip()]


def _names(text: str) -> set[str]:
    return {m.group(1) for m in _CALL.finditer(text)}


def _spring_oracles(body: str) -> tuple[int, int, list[tuple[int, int]]]:
    """MockMvc andExpect, WebTestClient/RestTestClient exchanges, Reactor StepVerifier."""
    strong = weak = 0
    handled: list[tuple[int, int]] = []
    for start, end in _statements(body):
        statement = body[start:end]
        mvc = list(_MVC_EXPECT.finditer(statement))
        exchange = _EXCHANGE.search(statement)
        steps = _STEP_VERIFIER.search(statement)
        if not (mvc or exchange or steps):
            continue
        handled.append((start, end))
        for match in mvc:
            close = _matching_paren(statement, match.end() - 1)
            for matcher in _split_args(statement[match.end():close]):
                status_only = _MVC_STATUS.match(matcher)
                if status_only or not _names(matcher) & set(MVC_STRONG):
                    weak += 1
                else:
                    strong += 1
        if exchange:
            names = _names(statement[exchange.start():])
            if names & set(EXCHANGE_STRONG):
                strong += 1
            else:
                weak += 1
        if steps:
            if _names(statement) & set(STEP_STRONG):
                strong += 1
            else:
                weak += 1
    return strong, weak, handled


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
