"""qr lint instructions and qr spec trace."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from quality_router.harness.instructions import lint_instructions
from quality_router.harness.spec_trace import collect_test_text, trace_spec

Write = Callable[[str, str], Path]


def codes(result) -> list[str]:
    return [f.code for f in result.findings]


class TestInstructionLint:
    def test_clean_file_passes(self, tmp_path: Path, write: Write) -> None:
        write("src/main/java/com/acme/App.java", "class App {}\n")
        write("AGENTS.md", "# Agents\nBuild: `mvn -B verify`. Code in `src/main/java`.\n"
                           "Entry: `com.acme.App`. Media: `application/json`.\n"
                           "```\n`missing/in/fence.md`\n```\n")
        result = lint_instructions(tmp_path)
        assert result.passed and result.findings == []

    def test_stale_refs_bloat_prose_rules_and_style(self, tmp_path: Path, write: Write) -> None:
        write("src/keep.txt", "")
        body = "\n".join([
            "See `src/gone/Old.java` and `docs/missing.md` and `com.acme.Gone`.",
            "Ignore `target/*.jar` and `unrelated/path` and `build.gradle`.",
            "Report at `target/site/jacoco/jacoco.xml` after the build.",
            "Never force push to main.",
            "Do not log PHI values.",
            "Use 4 spaces for indentation.",
        ] + ["filler"] * 10)
        write("AGENTS.md", body)
        write(".quality-router/policy.json", json.dumps({"deny_commands": ["force push"]}))
        result = lint_instructions(tmp_path, max_lines=5)
        found = codes(result)
        assert found.count("stale_reference") == 4
        assert "context_bloat" in found and "lint_leakage" in found
        prose = [f for f in result.findings if f.code == "prose_only_rule"]
        assert [f.line for f in prose] == [5]
        assert not result.passed

    def test_divergent_host_files(self, tmp_path: Path, write: Write) -> None:
        write("AGENTS.md", "# canonical\n")
        write("CLAUDE.md", "@AGENTS.md\n")
        write("GEMINI.md", "own rules\n")
        write(".cursor/rules/x.mdc", "rule\n")
        result = lint_instructions(tmp_path, strict=True)
        divergent = [f.path for f in result.findings if f.code == "divergent_instructions"]
        assert divergent == ["GEMINI.md"]
        assert not result.passed
        assert ".cursor/rules/x.mdc" in result.summary["files"]

    def test_no_canonical_and_no_files(self, tmp_path: Path, write: Write) -> None:
        assert codes(lint_instructions(tmp_path)) == ["no_instruction_file"]
        write("CLAUDE.md", "a\n")
        write("GEMINI.md", "b\n")
        assert codes(lint_instructions(tmp_path)) == ["no_canonical_instructions"]

    def test_bad_policy_json_is_ignored(self, tmp_path: Path, write: Write) -> None:
        write("AGENTS.md", "Never push secrets.\n")
        write(".quality-router/policy.json", "{not json")
        assert codes(lint_instructions(tmp_path)) == ["prose_only_rule"]


SPEC = """\
# Content item v2

- AC-1 Ingest accepts SCORM packages.
- AC-2 Normalized items carry a `licenseId`.
- The delivery API MUST NOT expose draft items (AC-3).
- Items SHALL be idempotent on re-ingest. [check: IdempotencyArchTest]
- Logs MUST NOT contain learner names.

```
AC-9 inside a fence is ignored. MUST ignore.
```
"""


class TestSpecTrace:
    def test_trace_map_and_findings(self, tmp_path: Path, write: Write) -> None:
        spec = write("specs/item.md", SPEC)
        write("ingest/src/test/java/IngestTest.java", '@Tag("AC-1") void a() {}\n'
                                                       "// AC-3 checked here\n")
        write("delivery/src/test/java/DeliveryTest.java", '@DisplayName("AC-10 other")\n')
        write("delivery/src/test/resources/fixture.json", '"AC-2"')
        result = trace_spec([spec], [tmp_path / "ingest", tmp_path / "delivery"],
                            max_constraints=2)
        assert result.summary["trace"]["AC-1"] == [str(tmp_path /
                                                        "ingest/src/test/java/IngestTest.java")]
        assert result.summary["trace"]["AC-2"] == []
        assert result.summary["criteria"] == 3 and result.summary["criteria_traced"] == 2
        assert codes(result) == ["unchecked_constraint", "constraint_load", "untraced_criterion"]
        assert result.summary["constraints"] == 3 and result.summary["constraints_unchecked"] == 1
        assert not result.passed

    def test_custom_pattern_and_no_criteria(self, tmp_path: Path, write: Write) -> None:
        spec = write("s.md", "REQ-7 must work.\n")
        test = write("T.java", "// REQ-7\n")
        result = trace_spec([spec], [test], id_pattern=r"\b(REQ)-\d+")
        assert result.summary["trace"] == {"REQ-7": [str(test)]}
        empty = trace_spec([write("e.md", "nothing\n")], [tmp_path], strict=True)
        assert codes(empty) == ["no_acceptance_criteria"] and not empty.passed

    def test_collect_skips_non_test_suffixes(self, tmp_path: Path, write: Write) -> None:
        write("src/test/java/A.java", "x")
        write("src/test/resources/a.bin", "x")
        write("features/login.feature", "x")
        assert sorted(Path(p).name for p in collect_test_text([tmp_path])) == [
            "A.java", "login.feature"]
