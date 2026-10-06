"""Generate JUnit Jupiter (5.8+ / 6) acceptance tests from a spec's example tables.

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


NULL_MARKERS = ("(null)", "(nil)", "(none)", "<null>")
TEXT_BLOCK_RELEASE = 15


def null_marker(table: ExampleTable) -> str:
    """JUnit maps nullValues even when quoted, so a literal "(null)" needs another marker."""
    literals = {cell_value(c) for row in table.rows for c in row}
    for marker in NULL_MARKERS:
        if marker not in literals:
            return marker
    raise ScaffoldError(f"every null marker {NULL_MARKERS} is also a literal value")


def _csv_cell(value: str | None, null: str = "(null)") -> str:
    if value is None:
        return null
    # '#' first would make the row a CSV comment and silently drop the example.
    needs_quotes = (value == "" or value != value.strip() or "'" in value or "|" in value
                    or value.startswith("#") or value in NULL_MARKERS)
    if needs_quotes:
        return "'" + value.replace("'", "''") + "'"
    return value


def _text_block_line(cells: list[str]) -> str:
    return " | ".join(cells).replace("\\", "\\\\").replace('"""', '\\"""')


def _csv_source(rows: list[list[str]], null: str, java_release: int) -> list[str]:
    head = f"    @CsvSource(delimiter = '|', nullValues = {_java_string(null)}, "
    if java_release >= TEXT_BLOCK_RELEASE:
        return [head + 'textBlock = """',
                *[f"            {_text_block_line(r)}" for r in rows],
                '            """',
                "    )"]
    values = [f"            {_java_string(' | '.join(r))}," for r in rows]
    values[-1] = values[-1].rstrip(",")
    return [head + "value = {", *values, "    })"]


def _bind_for(binds: dict[str, str], ac: str, column: str) -> str | None:
    return binds.get(f"{ac}.{column}") or binds.get(ac) or binds.get("*")


def _test_method(criterion: Criterion, table: ExampleTable, index: int,
                 binds: dict[str, str], java_release: int) -> tuple[list[str], bool]:
    params = [java_identifier(h, f"col{i}") for i, h in enumerate(table.headers)]
    if len(set(params)) != len(params):
        raise ScaffoldError(f"{criterion.id}: column names collide as Java identifiers: {params}")
    name = method_name(criterion.id) + (f"_{index + 1}" if index else "")
    null = null_marker(table)
    rows = [[_csv_cell(cell_value(c), null) for c in row] for row in table.rows]
    signature = ", ".join(f"String {p}" for p in params)
    display = f"{criterion.id} {criterion.title}".strip()
    out = [
        f"    @ParameterizedTest(name = {_java_string(criterion.id + ' [{index}] {arguments}')})",
        f"    @Tag({_java_string(criterion.id)})",
        f"    @DisplayName({_java_string(display)})",
        *_csv_source(rows, null, java_release),
        f"    void {name}({signature}) throws Exception {{",
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


SPRING_BOOT_TEST_IMPORTS = ("org.springframework.beans.factory.annotation.Autowired",
                            "org.springframework.boot.test.context.SpringBootTest")
_IMPORT = re.compile(r"(?:static\s+)?[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*(?:\.\*)?")
_ANNOTATION = re.compile(r"@[A-Za-z_][\w.]*(?:\(.*\))?")
MIN_JAVA_RELEASE = 8


@dataclass(frozen=True)
class TestContext:
    """Class-level wiring so a bind expression can reach a Spring bean or a fixture."""

    __test__ = False

    annotations: tuple[str, ...] = ()
    fields: tuple[str, ...] = ()
    imports: tuple[str, ...] = ()

    @classmethod
    def spring_boot_test(cls, annotations: tuple[str, ...] = (), fields: tuple[str, ...] = (),
                         imports: tuple[str, ...] = ()) -> TestContext:
        if not any(a.startswith(("@SpringBootTest", "@org.springframework.boot.test."))
                   for a in annotations):
            annotations = ("@SpringBootTest", *annotations)
        return cls(annotations, fields, (*SPRING_BOOT_TEST_IMPORTS, *imports))

    def validate(self) -> None:
        for imp in self.imports:
            if not _IMPORT.fullmatch(imp.strip()):
                raise ScaffoldError(f"--import is not a Java type or package name: {imp!r}")
        for ann in self.annotations:
            if "\n" in ann or not _ANNOTATION.fullmatch(ann.strip()):
                raise ScaffoldError(f"--class-annotation must look like @Name or @Name(...): "
                                    f"{ann!r}")
        for fld in self.fields:
            if "\n" in fld or not fld.strip().rstrip(";").strip():
                raise ScaffoldError(f"--field must be one declaration line: {fld!r}")


def _imports(context: TestContext) -> list[str]:
    statics = ["import static org.junit.jupiter.api.Assertions.assertEquals;"]
    plain = ["import java.util.Objects;", "import org.junit.jupiter.api.DisplayName;",
             "import org.junit.jupiter.api.Tag;",
             "import org.junit.jupiter.params.ParameterizedTest;",
             "import org.junit.jupiter.params.provider.CsvSource;"]
    for imp in context.imports:
        line = f"import {imp.strip().removesuffix(';')};"
        target = statics if line.startswith("import static ") else plain
        if line not in target:
            target.append(line)
    return [*sorted(statics), "", *sorted(plain)]


def scaffold_tests(doc: SpecDoc, package: str, class_name: str, binds: dict[str, str],
                   only: list[str] | None = None, java_release: int = 17,
                   context: TestContext | None = None) -> Scaffold:
    """Acceptance test source. java_release < 15 uses `value = {...}` instead of a text block."""
    if java_release < MIN_JAVA_RELEASE:
        raise ScaffoldError(f"--java-release must be >= {MIN_JAVA_RELEASE} (JUnit 5 baseline)")
    context = context or TestContext()
    context.validate()
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
            lines, bound = _test_method(criterion, table, index, binds, java_release)
            if body:
                body.append("")
            body.extend(lines)
            if not bound and criterion.id not in unbound:
                unbound.append(criterion.id)
    header = [f"package {package};", ""] if package else []
    fields = [f"    {f.strip().removesuffix(';').rstrip()};" for f in context.fields]
    source = "\n".join([
        *header,
        *_imports(context),
        "",
        f"// Generated by `qr spec scaffold` from {doc.path.name} (sha256 {digest}).",
        "// Rows are the spec's examples: change the spec, not this table. Bind, review,",
        "// then `qr spec lock`; the implementing change may not edit this file.",
        *[a.strip() for a in context.annotations],
        f"class {class_name} {{",
        "",
        *([*fields, ""] if fields else []),
        *body,
        "}",
        "",
    ])
    return Scaffold(source=source, criteria=[c.id for c in with_rows], unbound=unbound)
