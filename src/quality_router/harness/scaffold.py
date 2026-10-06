"""Generate JUnit 5 acceptance tests from a spec's example tables.

The rows come from the spec, not from the agent that writes the code
(P15: self-consistent wrong tests; 2605.17242: tests derived from the
requirements, approved, then looped against). A human binds each criterion
to the system under test with one expression (`--bind`), reviews, and
locks the file with `qr spec lock`. Unbound criteria fail (red first).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from quality_router.harness.specdoc import Criterion, ExampleTable, SpecDoc, cell_value


class ScaffoldError(ValueError):
    pass


@dataclass(frozen=True)
class Scaffold:
    source: str
    criteria: list[str]
    unbound: list[str]


def java_identifier(text: str, fallback: str = "value") -> str:
    words = [w for w in re.split(r"[^0-9A-Za-z]+", text) if w]
    if not words:
        return fallback
    ident = words[0][0].lower() + words[0][1:] + "".join(w[0].upper() + w[1:] for w in words[1:])
    return f"_{ident}" if ident[0].isdigit() else ident


def method_name(ac: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "_", ac).strip("_").lower()


def _java_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _csv_cell(value: str | None) -> str:
    if value is None:
        return "(null)"
    needs_quotes = (value == "" or value != value.strip() or "'" in value
                    or value == "(null)")
    if needs_quotes:
        return "'" + value.replace("'", "''") + "'"
    return value


def _text_block_line(cells: list[str]) -> str:
    return " | ".join(cells).replace("\\", "\\\\").replace('"""', '\\"""')


def _bind_for(binds: dict[str, str], ac: str, column: str) -> str | None:
    return binds.get(f"{ac}.{column}") or binds.get(ac) or binds.get("*")


def _test_method(criterion: Criterion, table: ExampleTable, index: int,
                 binds: dict[str, str]) -> tuple[list[str], bool]:
    params = [java_identifier(h, f"col{i}") for i, h in enumerate(table.headers)]
    if len(set(params)) != len(params):
        raise ScaffoldError(f"{criterion.id}: column names collide as Java identifiers: {params}")
    name = method_name(criterion.id) + (f"_{index + 1}" if index else "")
    rows = [_text_block_line([_csv_cell(cell_value(c)) for c in row]) for row in table.rows]
    signature = ", ".join(f"String {p}" for p in params)
    display = f"{criterion.id} {criterion.title}".strip()
    out = [
        f"    @ParameterizedTest(name = {_java_string(criterion.id + ' [{index}] {arguments}')})",
        f"    @Tag({_java_string(criterion.id)})",
        f"    @DisplayName({_java_string(display)})",
        "    @CsvSource(delimiter = '|', nullValues = \"(null)\", textBlock = \"\"\"",
        *[f"            {row}" for row in rows],
        '            """',
        "    )",
        f"    void {name}({signature}) {{",
    ]
    bound = True
    for col in table.outputs:
        column = table.column_name(col)
        expr = _bind_for(binds, criterion.id, column)
        if expr is None:
            bound = False
            ident = java_identifier(column, f"col{col}")
            expr = f"actual{ident[0].upper() + ident[1:]}"
            out.append(f"        Object {expr} = null; // bind {criterion.id}: call the system "
                       "under test with " + ", ".join(params[i] for i in table.inputs))
        out.append(f"        assertEquals({params[col]}, Objects.toString({expr}, null));")
    out.append("    }")
    return out, bound


def scaffold_tests(doc: SpecDoc, package: str, class_name: str, binds: dict[str, str],
                   only: list[str] | None = None) -> Scaffold:
    wanted = [c for c in doc.criteria if not only or c.id in only]
    missing = sorted(set(only or []) - {c.id for c in doc.criteria})
    if missing:
        raise ScaffoldError(f"criteria not in spec: {missing}")
    with_rows = [c for c in wanted if any(t.rows for t in c.tables)]
    if not with_rows:
        raise ScaffoldError("no selected criterion has an example table")
    digest = hashlib.sha256("\n".join(doc.lines).encode()).hexdigest()[:12]
    body: list[str] = []
    unbound: list[str] = []
    for criterion in with_rows:
        tables = [t for t in criterion.tables if t.rows]
        for index, table in enumerate(tables):
            lines, bound = _test_method(criterion, table, index, binds)
            if body:
                body.append("")
            body.extend(lines)
            if not bound and criterion.id not in unbound:
                unbound.append(criterion.id)
    header = [f"package {package};", ""] if package else []
    source = "\n".join([
        *header,
        "import static org.junit.jupiter.api.Assertions.assertEquals;",
        "",
        "import java.util.Objects;",
        "import org.junit.jupiter.api.DisplayName;",
        "import org.junit.jupiter.api.Tag;",
        "import org.junit.jupiter.params.ParameterizedTest;",
        "import org.junit.jupiter.params.provider.CsvSource;",
        "",
        f"// Generated by `qr spec scaffold` from {doc.path.name} (sha256 {digest}).",
        "// Rows are the spec's examples: change the spec, not this table. Bind, review,",
        "// then `qr spec lock`; the implementing change may not edit this file.",
        f"class {class_name} {{",
        "",
        *body,
        "}",
        "",
    ])
    return Scaffold(source=source, criteria=[c.id for c in with_rows], unbound=unbound)
