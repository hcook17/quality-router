"""The examples/content-pipeline fixture stays consistent with the gates (no JDK needed)."""

from __future__ import annotations

from pathlib import Path

from quality_router.harness.contracts import run_contract_check
from quality_router.harness.instructions import lint_instructions
from quality_router.harness.spec_trace import trace_spec

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


def test_base_instructions_flag_only_the_stale_mapper() -> None:
    lint = lint_instructions(EXAMPLE / "repos/content-normalize")
    errors = [f for f in lint.findings if f.level == "error"]
    assert [(f.code, f.line) for f in errors] == [("stale_reference", 7)]
