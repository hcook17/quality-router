"""Turn JUnit XML failures into short, criterion-aware repair feedback for an agent.

Engineering judgment, not an established lever. 2609.00362 found raw JUnit 4
feedback no better than "tests failed" for Java logic bugs (weak, n=50);
2609.22222 found thin diagnostics added nothing beyond the retry budget
(~35 runs). This output tests the obvious hypothesis (expected/actual, app
frames, the failing spec example); measure it with `qr eval`. Reads Surefire/Gradle/console
launcher XML reports, like JaCoCo XML; never runs or relays the build.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path

from quality_router.harness.javasrc import test_methods as find_test_methods
from quality_router.harness.scaffold import method_name
from quality_router.harness.specdoc import DEFAULT_ID_PATTERN, SpecDoc

FRAMEWORK_PREFIXES = (
    "java.", "javax.", "jdk.", "sun.", "com.sun.", "org.junit.", "junit.", "org.opentest4j.",
    "org.assertj.", "org.hamcrest.", "org.mockito.", "net.bytebuddy.", "org.apache.maven.",
    "org.gradle.", "worker.org.gradle.", "org.springframework.test.",
)
_EXPECTED = re.compile(r"expected:\s*<(.*?)>\s*but was:\s*<(.*?)>", re.DOTALL)
_EXPECTED_BARE = re.compile(r"expected:\s*(.*?)\s+but was:\s*(.*)", re.DOTALL)
_INVOCATION = re.compile(r"\[(\d+)\]")
_TEXT_BLOCK = re.compile(r'textBlock\s*=\s*"""')


@dataclass
class Example:
    spec: str
    line: int
    cells: list[str]


@dataclass
class Failure:
    classname: str
    method: str
    kind: str
    type: str
    message: str
    invocation: int | None = None
    expected: str | None = None
    actual: str | None = None
    frames: list[str] = field(default_factory=list)
    source: str = ""
    line: int = 0
    criteria: list[str] = field(default_factory=list)
    title: str = ""
    test_row: str = ""
    example: Example | None = None


def _method(name: str) -> str:
    return re.split(r"[(\[]", name, maxsplit=1)[0].strip()


def _frames(stack: str, max_frames: int) -> list[str]:
    kept: list[str] = []
    for raw in stack.splitlines():
        line = raw.strip()
        if line.startswith("Caused by:"):
            kept.append(line)
        elif line.startswith("at "):
            target = line[3:]
            if not target.startswith(FRAMEWORK_PREFIXES):
                kept.append(line)
        if len(kept) >= max_frames:
            break
    return kept


def parse_reports(paths: list[Path], max_frames: int = 5) -> tuple[int, list[Failure]]:
    """(test cases seen, failures) across JUnit XML reports."""
    total = 0
    failures: list[Failure] = []
    for path in paths:
        root = ET.parse(path).getroot()
        for case in root.iter("testcase"):
            total += 1
            problem = next((child for child in case if child.tag in ("failure", "error")), None)
            if problem is None:
                continue
            name = case.get("name", "")
            message = problem.get("message") or ""
            stack = problem.text or ""
            invocation = _INVOCATION.search(name)
            failure = Failure(
                classname=case.get("classname", ""),
                method=_method(name),
                kind=problem.tag,
                type=problem.get("type", ""),
                message=message.strip().splitlines()[0] if message.strip() else "",
                invocation=int(invocation.group(1)) if invocation else None,
                frames=_frames(stack, max_frames),
            )
            match = _EXPECTED.search(message) or _EXPECTED_BARE.search(message)
            if match:
                failure.expected, failure.actual = match.group(1), match.group(2).strip()
            failures.append(failure)
    return total, failures


def _source_for(classname: str, roots: list[Path]) -> Path | None:
    rel = Path(*classname.split("$", 1)[0].split(".")).with_suffix(".java")
    for root in roots:
        direct = root / rel
        if direct.is_file():
            return direct
        hit = next(iter(sorted(root.glob(f"**/{rel.as_posix()}"))), None)
        if hit is not None:
            return hit
    return None


def _csv_row(lines: list[str], start: int, end: int, invocation: int) -> str:
    rows: list[str] = []
    inside = False
    for line in lines[start - 1:end]:
        if not inside:
            inside = bool(_TEXT_BLOCK.search(line))
            continue
        text = line.strip()
        if text.startswith('"""'):
            break
        if text and not text.startswith("#"):
            rows.append(text)
    return rows[invocation - 1] if 0 < invocation <= len(rows) else ""


def enrich(failures: list[Failure], sources: list[Path], specs: list[SpecDoc],
           id_pattern: str = DEFAULT_ID_PATTERN) -> None:
    """Attach test location, criterion ids/title, CSV row, and the spec example row."""
    id_re = re.compile(r"(?<![\w-])(" + id_pattern + r")(?![\w.])")
    titles = {c.id: c.title for doc in specs for c in doc.criteria}
    examples: dict[str, tuple[SpecDoc, list]] = {}
    for doc in specs:
        for criterion in doc.criteria:
            tables = [t for t in criterion.tables if t.rows]
            for index, table in enumerate(tables):
                name = method_name(criterion.id) + (f"_{index + 1}" if index else "")
                examples[name] = (doc, [criterion, table])
    for failure in failures:
        path = _source_for(failure.classname, sources)
        if path is not None:
            source = path.read_text(encoding="utf-8", errors="replace")
            lines = source.splitlines()
            method = next((m for m in find_test_methods(source) if m.name == failure.method), None)
            if method is not None:
                failure.source, failure.line = str(path), method.start_line
                text = "\n".join(lines[method.start_line - 1:method.end_line])
                failure.criteria = sorted({m.group(1) for m in id_re.finditer(text)})
                if failure.invocation:
                    failure.test_row = _csv_row(lines, method.start_line, method.end_line,
                                                failure.invocation)
        if failure.method in examples:
            doc, (criterion, table) = examples[failure.method]
            failure.criteria = failure.criteria or [criterion.id]
            if failure.invocation and failure.invocation <= len(table.rows):
                i = failure.invocation - 1
                failure.example = Example(str(doc.path), table.row_lines[i], table.rows[i])
        failure.title = " / ".join(titles[c] for c in failure.criteria if titles.get(c))


def render_text(total: int, failures: list[Failure]) -> str:
    out: list[str] = []
    for f in failures:
        head = " ".join(f.criteria) or f"{f.classname}.{f.method}"
        out.append(f"FAIL {head}" + (f" {f.title}" if f.title else "")
                   + (f" [invocation {f.invocation}]" if f.invocation else ""))
        where = f"{f.source}:{f.line}" if f.source else "source not found (pass --sources)"
        out.append(f"  test     {f.classname}.{f.method} ({where})")
        if f.example:
            out.append(f"  example  {f.example.spec}:{f.example.line} | "
                       + " | ".join(f.example.cells) + " |")
        elif f.test_row:
            out.append(f"  row      {f.test_row}")
        if f.expected is not None:
            out.append(f"  assert   expected <{f.expected}> but was <{f.actual}>")
        else:
            out.append(f"  {f.kind:<8} {f.type}: {f.message}".rstrip(": "))
        out.extend(f"  {frame}" for frame in f.frames)
        if f.criteria:
            out.append("  next     change the code under test, not the spec-derived test")
        out.append("")
    verdict = "fail" if failures else "pass"
    out.append(f"junit_tests={total} failures={len(failures)} result={verdict}")
    return "\n".join(out) + "\n"


def render_json(total: int, failures: list[Failure]) -> str:
    payload = {"tests": total, "failed": len(failures), "passed": not failures,
               "failures": [asdict(f) for f in failures]}
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
