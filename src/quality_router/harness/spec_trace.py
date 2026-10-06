"""Trace spec acceptance criteria and RFC-2119 constraints to executable checks.

Evidence: P34 (structured acceptance criteria help: 2609.22222, 2605.17242),
2605.06445 (constraint decay: more prose constraints -> worse backend agents),
2607.18057 (tie each criterion to a test that executes changed lines).
A spec is useful to an agent only where something mechanical checks it.
"""

from __future__ import annotations

import re
from pathlib import Path

from quality_router.harness.report import GateResult

DEFAULT_ID_PATTERN = r"\bAC-\d+(?:\.\d+)?\b"
TEST_GLOBS = ("**/src/test/**/*", "**/src/it/**/*", "**/*.feature")
TEST_SUFFIXES = (".java", ".kt", ".groovy", ".feature", ".scala", ".py", ".ts", ".js")
_CONSTRAINT = re.compile(r"\b(MUST(?: NOT)?|SHALL(?: NOT)?|REQUIRED)\b")
_CHECK_TAG = re.compile(r"\[check:\s*([^\]]+)\]", re.IGNORECASE)


def collect_test_text(roots: list[Path]) -> dict[str, str]:
    texts: dict[str, str] = {}
    for root in roots:
        candidates = [root] if root.is_file() else [
            p for pattern in TEST_GLOBS for p in root.glob(pattern)
        ]
        for path in candidates:
            if path.is_file() and path.suffix in TEST_SUFFIXES:
                texts[str(path)] = path.read_text(encoding="utf-8", errors="replace")
    return texts


def trace_spec(
    specs: list[Path],
    test_roots: list[Path],
    id_pattern: str = DEFAULT_ID_PATTERN,
    max_constraints: int = 10,
    strict: bool = False,
) -> GateResult:
    result = GateResult(gate="spec-trace", strict=strict)
    ac_re = re.compile(id_pattern)
    tests = collect_test_text(test_roots)
    defined: dict[str, tuple[str, int]] = {}
    constraints = unchecked = 0
    for spec in specs:
        in_fence = False
        spec_constraints = 0
        for nr, line in enumerate(spec.read_text(encoding="utf-8").splitlines(), start=1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            ids = [m.group(0) for m in ac_re.finditer(line)]
            for ac in ids:
                defined.setdefault(ac, (str(spec), nr))
            if _CONSTRAINT.search(line):
                constraints += 1
                spec_constraints += 1
                if not ids and not _CHECK_TAG.search(line):
                    unchecked += 1
                    result.add("warning", "unchecked_constraint",
                               "MUST/SHALL with no AC id or [check: ...] tag; pair it with a "
                               "test, ArchUnit rule, or static check", str(spec), nr)
        if spec_constraints > max_constraints:
            result.add("warning", "constraint_load",
                       f"{spec_constraints} MUST/SHALL statements > {max_constraints}; split the "
                       "spec or move structural rules into deterministic checks", str(spec))
    traced: dict[str, list[str]] = {}
    for ac, (spec_path, nr) in sorted(defined.items()):
        id_re = re.compile(r"(?<![\w-])" + re.escape(ac) + r"(?![\w.])")
        hits = sorted(path for path, text in tests.items() if id_re.search(text))
        traced[ac] = hits
        if not hits:
            result.add("error", "untraced_criterion",
                       f"{ac} is not referenced by any test (tag it, e.g. @Tag(\"{ac}\"))",
                       spec_path, nr)
    if not defined:
        result.add("warning", "no_acceptance_criteria",
                   f"no ids matching {id_pattern!r}; number acceptance criteria (AC-1, AC-2, ...)")
    result.summary.update({
        "criteria": len(defined),
        "criteria_traced": sum(1 for hits in traced.values() if hits),
        "constraints": constraints,
        "constraints_unchecked": unchecked,
        "test_files_scanned": len(tests),
        "trace": traced,
    })
    return result
