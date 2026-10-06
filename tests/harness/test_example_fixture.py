"""The examples/content-pipeline fixture stays consistent with the gates (no JDK needed)."""

from __future__ import annotations

from pathlib import Path

from quality_router.harness.contracts import run_contract_check
from quality_router.harness.instructions import lint_instructions
from quality_router.harness.scaffold import scaffold_tests
from quality_router.harness.spec_trace import trace_spec
from quality_router.harness.specdoc import lint_spec, parse_spec

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "content-pipeline"


def test_base_contracts_are_in_sync() -> None:
    result = run_contract_check(EXAMPLE / "coordination/contracts.json", EXAMPLE / "repos")
    assert result.findings == []
    assert result.summary["merge_order"][:2] == ["content-ingest", "content-normalize"]


def test_base_spec_is_partially_traced() -> None:
    repos = EXAMPLE / "repos"
    result = trace_spec([EXAMPLE / "coordination/specs/content-item-v2.md"],
                        [repos / "content-normalize", repos / "content-delivery"])
    untraced = sorted(f.message.split()[0] for f in result.findings
                      if f.code == "untraced_criterion")
    assert untraced == ["AC-2", "AC-3"]


def test_prose_draft_fails_lint_executable_spec_passes() -> None:
    draft = lint_spec([EXAMPLE / "drafts/content-item-v2.md"])
    assert sorted({f.code for f in draft.findings if f.level == "error"}) == [
        "criterion_without_examples", "unresolved_placeholder"]
    spec = lint_spec([EXAMPLE / "coordination/specs/content-item-v2.md"], [EXAMPLE / "repos"])
    assert spec.passed and spec.findings == []
    assert spec.summary["examples"] == 12


def test_executable_spec_scaffolds_the_demo_acceptance_test() -> None:
    doc = parse_spec(EXAMPLE / "coordination/specs/content-item-v2.md")
    made = scaffold_tests(doc, "edu.acme.normalize", "ContentItemV2AcceptanceTest",
                          {"AC-1": "t(title)", "*": "l(manifest)"}, ["AC-1", "AC-2", "AC-3"])
    assert made.criteria == ["AC-1", "AC-2", "AC-3"] and made.unbound == []
    assert "            (null) | UNLICENSED\n" in made.source
    assert "            'license=  ' | UNLICENSED\n" in made.source


def test_base_instructions_flag_only_the_stale_mapper() -> None:
    lint = lint_instructions(EXAMPLE / "repos/content-normalize")
    errors = [f for f in lint.findings if f.level == "error"]
    assert [(f.code, f.line) for f in errors] == [("stale_reference", 7)]
