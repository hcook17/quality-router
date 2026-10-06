"""Executable specs: parse acceptance criteria with example tables, and lint spec quality.

Evidence: 2605.17242 (acceptance tests derived from requirements, approved,
then looped against: +15-24 pp, only with a reliable verifier), 2609.08149
(21 of 102 benchmark failures came from unstated constants, defaults and
ordering), 2609.22222 (a fully specified output contract swung scores 23 pp),
2605.06445 (structural constraints in prose make backend agents worse).

Spec format (markdown):
  Contract: `path/to/schema.json`
  ### AC-1 Title
  | input | expected output |
  | --- | --- |
  | `literal` | value |
Columns whose header starts with "expected " are outputs; with none, the last
column is the output. `(null)` is null; backticks keep a cell verbatim.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from quality_router.harness.report import GateResult

DEFAULT_ID_PATTERN = r"AC-\d+(?:\.\d+)?"
NULL_CELL = "(null)"
MAX_SPEC_LINES = 120

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
_TABLE_SEP = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
_CONTRACT = re.compile(r"^\s*(?:[-*]\s*)?\**contracts?\**\s*:\s*(.+)$", re.IGNORECASE)
_BACKTICK = re.compile(r"`([^`]+)`")
_CONSTRAINT = re.compile(r"\b(MUST(?: NOT)?|SHALL(?: NOT)?|REQUIRED)\b")
_CHECK_TAG = re.compile(r"\[check:\s*([^\]]+)\]", re.IGNORECASE)
_EXAMPLE_LINE = re.compile(r"\b(example|e\.g\.)\s*:?.*`[^`]+`", re.IGNORECASE)
_PLACEHOLDER = re.compile(r"\b(TBD|TBC|TODO|FIXME)\b|\?\?\?")
VAGUE_TERMS = (
    "appropriate", "appropriately", "reasonable", "reasonably", "properly", "as needed",
    "where possible", "if possible", "as appropriate", "gracefully", "user-friendly",
    "robust", "seamless", "seamlessly", "fast", "quickly", "efficient", "efficiently",
    "intuitive", "etc", "and so on", "and/or", "should handle",
    "handle correctly", "best effort", "state of the art", "flexible",
)
_VAGUE = re.compile(r"(?<![\w-])(" + "|".join(re.escape(t) for t in VAGUE_TERMS) + r")(?![\w-])",
                    re.IGNORECASE)
_STRUCTURAL = re.compile(
    r"\b(layer(ed)?|repository layer|DAO|ORM|JPA|Hibernate|transaction(al)?|database|SQL|"
    r"schema migration|Flyway|Liquibase|package structure|bean|Spring (config|context)|"
    r"architecture|hexagonal|clean architecture)\b",
    re.IGNORECASE,
)


@dataclass
class ExampleTable:
    line: int
    headers: list[str]
    rows: list[list[str]]
    row_lines: list[int]
    ragged: list[int] = field(default_factory=list)

    @property
    def outputs(self) -> list[int]:
        marked = [i for i, h in enumerate(self.headers) if h.lower().startswith("expected ")]
        return marked or [len(self.headers) - 1]

    @property
    def inputs(self) -> list[int]:
        out = set(self.outputs)
        return [i for i in range(len(self.headers)) if i not in out]

    def column_name(self, index: int) -> str:
        header = self.headers[index]
        return header[len("expected "):] if header.lower().startswith("expected ") else header


@dataclass
class Criterion:
    id: str
    title: str
    line: int
    body: list[tuple[int, str]] = field(default_factory=list)
    tables: list[ExampleTable] = field(default_factory=list)

    @property
    def has_inline_example(self) -> bool:
        texts = [self.title, *(text for _, text in self.body)]
        return any(_EXAMPLE_LINE.search(text) for text in texts)


@dataclass
class SpecDoc:
    path: Path
    lines: list[str]
    criteria: list[Criterion]
    contracts: list[tuple[int, str]]
    duplicates: list[tuple[str, int]]


def _cells(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|") and not text.endswith("\\|"):
        text = text[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", text)]


def _criterion_start(line: str, id_re: re.Pattern[str]) -> tuple[str, str] | None:
    heading = _HEADING.match(line)
    bullet = None if heading else _BULLET.match(line)
    text = heading.group(2) if heading else bullet.group(1) if bullet else None
    if text is None:
        return None
    text = text.strip().lstrip("*_").strip()
    match = id_re.match(text)
    if not match:
        return None
    title = text[match.end():].lstrip("*_").strip(" :.-–—*_")
    return match.group(0), title


def parse_spec(path: Path, id_pattern: str = DEFAULT_ID_PATTERN) -> SpecDoc:
    id_re = re.compile(id_pattern)
    lines = path.read_text(encoding="utf-8").splitlines()
    criteria: list[Criterion] = []
    contracts: list[tuple[int, str]] = []
    seen: dict[str, int] = {}
    duplicates: list[tuple[str, int]] = []
    current: Criterion | None = None
    in_fence = False
    i = 0
    while i < len(lines):
        line, nr = lines[i], i + 1
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            i += 1
            continue
        contract = _CONTRACT.match(line)
        if contract:
            contracts.extend((nr, ref) for ref in _BACKTICK.findall(contract.group(1)))
        start = _criterion_start(line, id_re)
        if start:
            ac, title = start
            if ac in seen:
                duplicates.append((ac, nr))
            seen.setdefault(ac, nr)
            current = Criterion(ac, title, nr)
            criteria.append(current)
            i += 1
            continue
        if _HEADING.match(line):
            current = None
        elif current is not None and line.strip().startswith("|"):
            i = _read_table(lines, i, current)
            continue
        elif current is not None and line.strip():
            current.body.append((nr, line))
        i += 1
    return SpecDoc(path, lines, criteria, contracts, duplicates)


def _read_table(lines: list[str], start: int, criterion: Criterion) -> int:
    block: list[tuple[int, str]] = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|"):
        block.append((i + 1, lines[i]))
        i += 1
    headers = _cells(block[0][1])
    body = block[1:]
    if body and _TABLE_SEP.match(body[0][1].strip()):
        body = body[1:]
    table = ExampleTable(line=block[0][0], headers=headers, rows=[], row_lines=[])
    for nr, raw in body:
        cells = _cells(raw)
        if len(cells) != len(headers):
            table.ragged.append(nr)
            continue
        table.rows.append(cells)
        table.row_lines.append(nr)
    criterion.tables.append(table)
    return i


def cell_value(cell: str) -> str | None:
    """Spec cell -> literal value. `(null)` is None; backticks keep inner text verbatim."""
    if cell == NULL_CELL:
        return None
    if len(cell) >= 2 and cell.startswith("`") and cell.endswith("`"):
        return cell[1:-1]
    return cell


def _resolve_contract(spec: Path, ref: str, roots: list[Path]) -> bool:
    candidates = [Path(ref)] if Path(ref).is_absolute() else [
        base / ref for base in (spec.parent, *spec.parent.parents, *roots)
    ]
    return any(c.is_file() for c in candidates)


def lint_spec(specs: list[Path], roots: list[Path] | None = None,
              id_pattern: str = DEFAULT_ID_PATTERN, strict: bool = False) -> GateResult:
    result = GateResult(gate="spec-lint", strict=strict)
    roots = roots or []
    totals = {"criteria": 0, "examples": 0}
    for spec in specs:
        doc = parse_spec(spec, id_pattern)
        rel = str(spec)
        totals["criteria"] += len(doc.criteria)
        if not doc.criteria:
            result.add("error", "no_acceptance_criteria",
                       f"no criteria headed by an id matching {id_pattern!r} "
                       "(e.g. `### AC-1 Title`)", rel)
        for ac, nr in doc.duplicates:
            result.add("error", "duplicate_criterion", f"{ac} defined twice", rel, nr)
        for criterion in doc.criteria:
            rows = sum(len(t.rows) for t in criterion.tables)
            totals["examples"] += rows
            if not rows:
                if criterion.has_inline_example:
                    result.add("info", "not_scaffoldable",
                               f"{criterion.id} has an inline example but no example table",
                               rel, criterion.line)
                else:
                    result.add("error", "criterion_without_examples",
                               f"{criterion.id}: add an example table with concrete inputs and "
                               "expected outputs (pins constants, defaults, ordering)",
                               rel, criterion.line)
            for table in criterion.tables:
                for nr in table.ragged:
                    result.add("error", "ragged_example_row",
                               f"{criterion.id}: row width differs from the header", rel, nr)
                if len(table.headers) < 2:
                    result.add("error", "example_table_needs_io",
                               f"{criterion.id}: need at least one input and one output column",
                               rel, table.line)
        if not doc.contracts:
            result.add("warning", "no_output_contract",
                       "no `Contract:` line; reference the JSON Schema/OpenAPI/Avro this spec "
                       "changes", rel)
        for nr, ref in doc.contracts:
            if not _resolve_contract(spec, ref, roots):
                result.add("error", "contract_not_found", f"`{ref}` not found", rel, nr)
        _lint_lines(doc, result, rel)
    result.summary.update(totals)
    result.summary["specs"] = len(specs)
    return result


SPEC_TEMPLATE = """\
# {title}

Contract: `{contract}`

Problem: one sentence from Research (who is blocked, what evidence).
Out of scope: what this change will not do.

### AC-1 Replace with an observable behaviour

| input | expected output |
| --- | --- |
| `concrete input` | concrete output |
| (null) | value for a missing input |

### AC-2 Replace with the next behaviour

| input | expected output |
| --- | --- |
| `edge case` | its exact output |

Structural rules (layering, persistence) go to ArchUnit, tagged [check: ArchUnitRuleName].
"""


def new_spec(title: str, contract: str = "contracts/CHANGE-ME.schema.json") -> str:
    return SPEC_TEMPLATE.format(title=title, contract=contract)


def _lint_lines(doc: SpecDoc, result: GateResult, rel: str) -> None:
    in_fence = False
    nonblank = 0
    for nr, line in enumerate(doc.lines, start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line.strip():
            continue
        nonblank += 1
        if line.strip().startswith("|"):
            continue
        prose = _BACKTICK.sub("", line)
        if _PLACEHOLDER.search(prose):
            result.add("error", "unresolved_placeholder",
                       "TBD/TODO in an approved spec; decide it or cut it", rel, nr)
        for match in _VAGUE.finditer(prose):
            result.add("warning", "vague_term",
                       f"{match.group(1)!r} is not testable; state the value or the example",
                       rel, nr)
        if (_CONSTRAINT.search(prose) and _STRUCTURAL.search(prose)
                and not _CHECK_TAG.search(prose)):
            result.add("warning", "structural_rule_in_prose",
                       "layer/persistence rule as spec prose; enforce it with ArchUnit or a "
                       "static check and tag it [check: ...]", rel, nr)
    if nonblank > MAX_SPEC_LINES:
        result.add("warning", "spec_too_long",
                   f"{nonblank} non-blank lines > {MAX_SPEC_LINES}; split by criterion", rel)
