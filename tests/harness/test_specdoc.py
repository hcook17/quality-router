"""qr spec lint / scaffold / new: executable specs and JUnit acceptance tests from examples."""

from __future__ import annotations

from pathlib import Path

import pytest

from quality_router.harness.scaffold import (
    NULL_MARKERS,
    ScaffoldError,
    TestContext,
    _csv_cell,
    java_identifier,
    method_name,
    scaffold_tests,
)
from quality_router.harness.specdoc import (
    MAX_SPEC_LINES,
    cell_value,
    lint_spec,
    new_spec,
    parse_spec,
)

GOOD = """\
# Content item v2

Contract: `contracts/item.schema.json`

### AC-1 Title is trimmed
| title | expected title |
| --- | --- |
| `  Intro  ` | Intro |
| a \\| b | a \\| b |

### AC-2: Missing license defaults
| manifest | expected licenseId |
|---|---|
| (null) | UNLICENSED |
| `license=` | UNLICENSED |
| `(null)` | `(null)` |

```
### AC-9 inside a fence is ignored
```

## Notes
| not | a criterion table |
"""


def codes(result) -> list[str]:
    return [f.code for f in result.findings]


@pytest.fixture
def good(write) -> Path:
    write("contracts/item.schema.json", "{}")
    return write("specs/item.md", GOOD)


class TestParse:
    def test_criteria_tables_and_cells(self, good: Path) -> None:
        doc = parse_spec(good)
        assert [c.id for c in doc.criteria] == ["AC-1", "AC-2"]
        assert doc.criteria[1].title == "Missing license defaults"
        table = doc.criteria[0].tables[0]
        assert table.outputs == [1] and table.inputs == [0]
        assert table.column_name(1) == "title"
        assert table.rows[1] == ["a | b", "a | b"]
        assert doc.contracts == [(3, "contracts/item.schema.json")]
        assert [cell_value(c) for c in doc.criteria[1].tables[0].rows[0]] == [None, "UNLICENSED"]
        assert cell_value("`  x `") == "  x "

    def test_bullets_and_default_output_column(self, write) -> None:
        spec = write("s.md", "- **AC-3.1** Delivers\n  | id | status |\n  | 1 | 200 |\n"
                             "- AC-4 next\n- AC-3.1 again\n")
        doc = parse_spec(spec)
        assert [c.id for c in doc.criteria] == ["AC-3.1", "AC-4", "AC-3.1"]
        assert doc.duplicates == [("AC-3.1", 5)]
        assert doc.criteria[0].tables[0].outputs == [1]
        assert doc.criteria[0].tables[0].rows == [["1", "200"]]


class TestLint:
    def test_clean_spec_passes(self, good: Path) -> None:
        result = lint_spec([good])
        assert result.passed, codes(result)
        assert result.summary == {"criteria": 2, "examples": 5, "specs": 1}

    def test_draft_spec_fails_with_reasons(self, write) -> None:
        write("big.md", "")
        spec = write("draft.md", "\n".join([
            "# Draft",
            "Contract: `nope.json`",
            "- AC-1 Normalize titles appropriately and handle errors gracefully",
            "- AC-2 Licence default. Example: `license=` -> `UNLICENSED`",
            "- AC-3 Ragged",
            "  | a | b |",
            "  | --- | --- |",
            "  | 1 |",
            "- AC-4 One column",
            "  | only |",
            "  | x |",
            "- AC-4 dup",
            "Default value is TBD.",
            "Writes MUST go through the repository layer.",
            "Reads MUST use the DAO [check: ArchUnitLayers].",
        ]))
        result = lint_spec([spec])
        found = codes(result)
        assert not result.passed
        for code in ("contract_not_found", "criterion_without_examples", "duplicate_criterion",
                     "ragged_example_row", "example_table_needs_io", "unresolved_placeholder",
                     "vague_term", "structural_rule_in_prose", "not_scaffoldable"):
            assert code in found, code
        assert found.count("structural_rule_in_prose") == 1
        assert found.count("vague_term") == 2

    def test_no_criteria_no_contract_too_long(self, write) -> None:
        spec = write("long.md", "\n".join(f"line {i}" for i in range(MAX_SPEC_LINES + 1)))
        result = lint_spec([spec], strict=True)
        assert {"no_acceptance_criteria", "no_output_contract", "spec_too_long"} <= set(
            codes(result))

    def test_contract_resolves_from_extra_root(self, write, tmp_path: Path) -> None:
        write("other/contracts/x.json", "{}")
        spec = write("specs/s.md",
                     "Contract: `contracts/x.json`\n### AC-1 t\n| a | b |\n| 1 | 2 |\n")
        assert "contract_not_found" in codes(lint_spec([spec]))
        assert lint_spec([spec], [tmp_path / "other"]).passed

    def test_template_is_scaffoldable(self, write) -> None:
        write("contracts/CHANGE-ME.schema.json", "{}")
        spec = write("t.md", new_spec("Item v2"))
        result = lint_spec([spec])
        assert result.passed, codes(result)
        assert "# Item v2" in spec.read_text()


class TestScaffold:
    def test_generates_parameterized_tests(self, good: Path) -> None:
        made = scaffold_tests(parse_spec(good), "com.acme", "ItemAcceptanceTest",
                              {"AC-1": "svc.title(title)"})
        src = made.source
        assert made.criteria == ["AC-1", "AC-2"] and made.unbound == ["AC-2"]
        assert src.startswith("package com.acme;")
        assert '@Tag("AC-1")' in src and '@DisplayName("AC-2 Missing license defaults")' in src
        assert "void ac_1(String title, String expectedTitle) {" in src
        assert "'  Intro  ' | Intro" in src
        # AC-2 has a literal "(null)" string, so its null marker moves to (nil).
        assert 'nullValues = "(nil)"' in src and 'nullValues = "(null)"' in src
        assert "(nil) | UNLICENSED" in src and "'(null)' | '(null)'" in src
        assert "assertEquals(expectedTitle, Objects.toString(svc.title(title), null));" in src
        assert "Object actualLicenseId = null; // bind AC-2: call the system under test with " \
               "manifest" in src
        assert "assertEquals(expectedLicenseId, Objects.toString(actualLicenseId, null));" in src
        assert 'textBlock = """' in src and '            """\n    )' in src

    def test_column_binds_and_wildcard(self, write) -> None:
        spec = write("s.md", "### AC-1 t\n| id | expected status | expected body |\n"
                             "|---|---|---|\n| 1 | 200 | ok |\n\n"
                             "| id | x |\n|---|---|\n| 2 | y |\n")
        made = scaffold_tests(parse_spec(spec), "", "T",
                              {"AC-1.status": "api.get(id).status()", "*": "api.other(id)"})
        assert not made.source.startswith("package")
        assert "Objects.toString(api.get(id).status(), null)" in made.source
        assert "Objects.toString(api.other(id), null)" in made.source
        assert "void ac_1_2(String id, String x)" in made.source
        assert made.unbound == []

    def test_errors(self, write, good: Path) -> None:
        with pytest.raises(ScaffoldError, match="not in spec"):
            scaffold_tests(parse_spec(good), "", "T", {}, only=["AC-7"])
        bare = write("bare.md", "### AC-1 no table\n")
        with pytest.raises(ScaffoldError, match="no selected"):
            scaffold_tests(parse_spec(bare), "", "T", {})
        clash = write("clash.md", "### AC-1 t\n| a b | a-b |\n|---|---|\n| 1 | 2 |\n")
        with pytest.raises(ScaffoldError, match="collide"):
            scaffold_tests(parse_spec(clash), "", "T", {})

    def test_helpers(self) -> None:
        assert java_identifier("expected license id") == "expectedLicenseId"
        assert java_identifier("1st") == "_1st" and java_identifier("--", "c0") == "c0"
        assert method_name("AC-2.1") == "ac_2_1"
        assert _csv_cell("") == "''" and _csv_cell("it's") == "'it''s'"
        assert _csv_cell(None) == "(null)" and _csv_cell("x") == "x"
        assert _csv_cell(None, "(nil)") == "(nil)"
        assert _csv_cell("a|b") == "'a|b'" and _csv_cell("#x") == "'#x'"
        assert _csv_cell("x # y") == "x # y" and _csv_cell("(nil)") == "'(nil)'"

    def test_null_marker_exhausted(self, write) -> None:
        cells = " | ".join(f"`{m}`" for m in NULL_MARKERS)
        spec = write("n.md", f"### AC-1 t\n| a | b | c | expected d |\n|---|---|---|---|\n"
                             f"| {cells} |\n")
        with pytest.raises(ScaffoldError, match="null marker"):
            scaffold_tests(parse_spec(spec), "", "T", {})


class TestScaffoldJavaReleaseAndContext:
    def test_array_form_below_java_15(self, good: Path) -> None:
        src = scaffold_tests(parse_spec(good), "", "T", {}, java_release=11).source
        assert 'textBlock' not in src and '"""' not in src
        assert "    @CsvSource(delimiter = '|', nullValues = \"(null)\", value = {" in src
        assert "            \"'  Intro  ' | Intro\",\n" in src
        assert "\n    })\n    void ac_1(" in src
        with pytest.raises(ScaffoldError, match=">= 8"):
            scaffold_tests(parse_spec(good), "", "T", {}, java_release=7)

    def test_array_form_escapes_java_strings(self, write) -> None:
        spec = write("e.md", '### AC-1 t\n| a | expected b |\n|---|---|\n'
                             '| `say "hi"` | `back\\slash` |\n')
        src = scaffold_tests(parse_spec(spec), "", "T", {}, java_release=8).source
        assert '"say \\"hi\\" | back\\\\slash"' in src

    def test_spring_boot_test_context(self, good: Path) -> None:
        context = TestContext.spring_boot_test(
            fields=("@Autowired ContentNormalizer normalizer;",),
            imports=("com.acme.normalize.ContentNormalizer", "static org.x.Y.z",
                     "org.springframework.beans.factory.annotation.Autowired"))
        src = scaffold_tests(parse_spec(good), "com.acme", "T",
                             {"AC-1": "normalizer.title(title)"}, context=context).source
        assert "\n@SpringBootTest\nclass T {\n\n    @Autowired ContentNormalizer normalizer;\n\n" \
            in src
        assert src.count("import org.springframework.beans.factory.annotation.Autowired;") == 1
        assert "import static org.x.Y.z;" in src
        assert "import com.acme.normalize.ContentNormalizer;" in src
        assert src.index("import org.springframework.boot") > src.index("import org.junit")

    def test_explicit_spring_boot_test_annotation_kept(self, good: Path) -> None:
        context = TestContext.spring_boot_test(
            annotations=("@SpringBootTest(classes = App.class)", '@ActiveProfiles("test")'))
        src = scaffold_tests(parse_spec(good), "", "T", {}, context=context).source
        assert '@SpringBootTest(classes = App.class)\n@ActiveProfiles("test")\nclass T' in src
        assert "\n@SpringBootTest\n" not in src

    @pytest.mark.parametrize("context, message", [
        (TestContext(imports=("com.acme; drop",)), "--import"),
        (TestContext(annotations=("SpringBootTest",)), "--class-annotation"),
        (TestContext(annotations=("@A\n@B",)), "--class-annotation"),
        (TestContext(fields=(" ; ",)), "--field"),
        (TestContext(fields=("A a;\nB b",)), "--field"),
    ])
    def test_context_validation(self, good: Path, context: TestContext, message: str) -> None:
        with pytest.raises(ScaffoldError, match=message):
            scaffold_tests(parse_spec(good), "", "T", {}, context=context)
