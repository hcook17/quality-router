"""Diff coverage over JaCoCo XML: are the lines this change touched executed by tests?

Evidence: 2607.18057 (tests cover 61.5% of agent-changed Java lines; 86% of
catch lines unexecuted). "mvn test is green" is not evidence the change ran.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from quality_router.harness.javasrc import catch_block_lines
from quality_router.harness.report import GateResult

TEST_DIR_MARKERS = ("/src/test/", "src/test/", "/src/it/", "src/it/")
BUILD_DIRS = ("target", "build")


@dataclass
class LineCov:
    covered_instr: int
    missed_instr: int
    covered_branches: int
    missed_branches: int


@dataclass
class JacocoReport:
    path: Path
    module_root: str
    lines: dict[str, dict[int, LineCov]] = field(default_factory=dict)


def parse_jacoco(xml_path: Path, cwd: Path) -> JacocoReport:
    tree = ET.parse(xml_path)
    report = JacocoReport(path=xml_path, module_root=_module_root(xml_path, cwd))
    for package in tree.getroot().iter("package"):
        pkg = package.get("name", "")
        for source in package.findall("sourcefile"):
            key = f"{pkg}/{source.get('name', '')}" if pkg else source.get("name", "")
            per_line = report.lines.setdefault(key, {})
            for line in source.findall("line"):
                per_line[int(line.get("nr", "0"))] = LineCov(
                    covered_instr=int(line.get("ci", "0")),
                    missed_instr=int(line.get("mi", "0")),
                    covered_branches=int(line.get("cb", "0")),
                    missed_branches=int(line.get("mb", "0")),
                )
    return report


def _module_root(xml_path: Path, cwd: Path) -> str:
    try:
        rel = xml_path.resolve().relative_to(cwd.resolve())
    except ValueError:
        return ""
    parts = rel.parts
    for i, part in enumerate(parts):
        if part in BUILD_DIRS:
            return "/".join(parts[:i])
    return ""


# Gradle JVM test suites and test fixtures: src/integrationTest/, src/functionalTest/, ...
_GRADLE_TEST_SET = re.compile(r"(?:^|/)src/(?:\w+Test|testFixtures)/")


def is_test_path(path: str) -> bool:
    return (any(marker in path if marker.startswith("/") else path.startswith(marker)
                for marker in TEST_DIR_MARKERS)
            or bool(_GRADLE_TEST_SET.search(path)))


def _match_report(path: str, reports: list[JacocoReport]) -> tuple[JacocoReport, str] | None:
    candidates: list[tuple[JacocoReport, str]] = []
    for report in reports:
        for key in report.lines:
            if path == key or path.endswith("/" + key):
                candidates.append((report, key))
    if len(candidates) <= 1:
        return candidates[0] if candidates else None
    scoped = [c for c in candidates if c[0].module_root and path.startswith(c[0].module_root + "/")]
    return max(scoped or candidates, key=lambda c: len(c[0].module_root))


def run_diff_coverage(
    changed: dict[str, set[int]],
    reports: list[JacocoReport],
    cwd: Path,
    minimum: float,
    catch_minimum: float | None,
    include_tests: bool = False,
) -> GateResult:
    result = GateResult(gate="diff-coverage")
    executable = covered = 0
    catch_exec = catch_cov = 0
    files_checked = 0
    for path in sorted(changed):
        if not path.endswith(".java") or (is_test_path(path) and not include_tests):
            continue
        match = _match_report(path, reports)
        if match is None:
            result.add("warning", "no_coverage_data",
                       "changed source has no JaCoCo entry (module not in any --jacoco report?)",
                       path)
            continue
        report, key = match
        files_checked += 1
        line_cov = report.lines[key]
        source_file = cwd / path
        catches = (catch_block_lines(source_file.read_text(encoding="utf-8"))
                   if source_file.is_file() else set())
        for nr in sorted(changed[path]):
            cov = line_cov.get(nr)
            if cov is None or (cov.covered_instr + cov.missed_instr) == 0:
                continue
            executable += 1
            hit = cov.covered_instr > 0
            covered += hit
            in_catch = nr in catches
            if in_catch:
                catch_exec += 1
                catch_cov += hit
            if not hit:
                code = "uncovered_catch_line" if in_catch else "uncovered_line"
                result.add("warning" if in_catch else "info", code,
                           "changed line not executed by any test", path, nr)
            elif cov.missed_branches:
                result.add("info", "partial_branch",
                           f"{cov.missed_branches} of {cov.missed_branches + cov.covered_branches}"
                           " branches not taken", path, nr)
    ratio = covered / executable if executable else 1.0
    catch_ratio = catch_cov / catch_exec if catch_exec else 1.0
    result.summary.update({
        "files_checked": files_checked,
        "changed_executable_lines": executable,
        "changed_covered_lines": covered,
        "diff_coverage": ratio,
        "catch_lines": catch_exec,
        "catch_covered": catch_cov,
        "min": minimum,
    })
    if ratio < minimum:
        result.add("error", "diff_coverage_below_min",
                   f"{covered}/{executable} changed executable lines covered "
                   f"({ratio:.1%} < {minimum:.0%})")
    if catch_minimum is not None and catch_ratio < catch_minimum:
        result.add("error", "catch_coverage_below_min",
                   f"{catch_cov}/{catch_exec} changed catch-block lines covered "
                   f"({catch_ratio:.1%} < {catch_minimum:.0%})")
    return result
