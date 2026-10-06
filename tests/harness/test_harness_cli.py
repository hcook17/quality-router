"""End-to-end `qr` argv for the phase-3 commands and the qr init --policy / --ci stamps."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from harness.helpers import git
from quality_router.cli import run
from quality_router.harness.ci import GITHUB_MAVEN_PATH, stamp_ci
from quality_router.harness.report import EXIT_FAIL, EXIT_PASS, EXIT_USAGE

LOADER = """\
package com.acme;
class Loader {
  int load() {
    return 1;
  }
}
"""
JACOCO = ('<report name="r"><package name="com/acme"><sourcefile name="Loader.java">'
          '<line nr="4" mi="0" ci="2" mb="0" cb="0"/></sourcefile></package></report>')
TEST = """\
class LoaderTest {
  @Test
  void loads() {
    assertNotNull(new Loader().load());
  }
}
"""


def stdin(monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(text))


@pytest.fixture
def java_repo(repo: Path) -> tuple[Path, str]:
    (repo / "README.md").write_text("x\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    base = git(repo, "rev-parse", "HEAD")
    src = repo / "src/main/java/com/acme/Loader.java"
    src.parent.mkdir(parents=True)
    src.write_text(LOADER)
    test = repo / "src/test/java/com/acme/LoaderTest.java"
    test.parent.mkdir(parents=True)
    test.write_text(TEST)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "loader")
    xml = repo / "target/site/jacoco/jacoco.xml"
    xml.parent.mkdir(parents=True)
    xml.write_text(JACOCO)
    return repo, base


class TestGateCommands:
    def test_diff_coverage_from_git(self, java_repo, capsys) -> None:
        repo, base = java_repo
        code = run(["gate", "diff-coverage", "--cwd", str(repo), "--base", base,
                    "--jacoco", "**/jacoco.xml", "--json"])
        payload = json.loads(capsys.readouterr().out)
        assert code == EXIT_PASS and payload["summary"]["reports"] == 1
        assert payload["summary"]["changed_executable_lines"] == 1

    def test_diff_coverage_usage_errors(self, java_repo, tmp_path, capsys, monkeypatch) -> None:
        repo, _ = java_repo
        assert run(["gate", "diff-coverage", "--cwd", str(repo), "--jacoco", "nope/*.xml",
                    "--base", "x"]) == EXIT_USAGE
        assert run(["gate", "diff-coverage", "--cwd", str(repo), "--jacoco",
                    str(repo / "missing.xml"), "--base", "x"]) == EXIT_USAGE
        xml = "target/site/jacoco/jacoco.xml"
        assert run(["gate", "diff-coverage", "--cwd", str(repo), "--jacoco", xml]) == EXIT_USAGE
        assert run(["gate", "diff-coverage", "--cwd", str(repo), "--jacoco", xml,
                    "--base", "no-such-ref"]) == EXIT_USAGE
        stdin(monkeypatch, "")
        assert run(["gate", "diff-coverage", "--cwd", str(repo), "--jacoco", xml,
                    "--diff", "-"]) == EXIT_PASS
        assert "git fetch" in capsys.readouterr().err

    def test_test_oracles(self, java_repo, capsys) -> None:
        repo, base = java_repo
        assert run(["gate", "test-oracles", "--cwd", str(repo), "--base", base]) == EXIT_FAIL
        assert "weak_oracle" in capsys.readouterr().out
        assert run(["gate", "test-oracles", "--cwd", str(repo), "--base", base,
                    "--allow-weak"]) == EXIT_PASS
        assert run(["gate", "test-oracles", "--cwd", str(repo), "--paths",
                    "src/test/java/com/acme/LoaderTest.java", "--assert-helper",
                    "assertNotNull"]) == EXIT_PASS
        assert run(["gate", "test-oracles", "--cwd", str(repo)]) == EXIT_USAGE


class TestLintSpecContracts:
    def test_lint(self, tmp_path: Path, capsys) -> None:
        (tmp_path / "AGENTS.md").write_text("Build with `mvn -B verify`.\n")
        assert run(["lint", "instructions", "--root", str(tmp_path)]) == EXIT_PASS
        assert run(["lint", "instructions", "--root", str(tmp_path / "nope")]) == EXIT_USAGE

    def test_spec_trace(self, tmp_path: Path, monkeypatch, capsys) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "specs").mkdir()
        (tmp_path / "specs/a.md").write_text("AC-1 works\n")
        test = tmp_path / "src/test/java/ATest.java"
        test.parent.mkdir(parents=True)
        test.write_text('@Tag("AC-1")\n')
        assert run(["spec", "trace", "--spec", "specs/*.md", "--tests", "."]) == EXIT_PASS
        assert run(["spec", "trace", "--spec", "nope.md", "--tests", "."]) == EXIT_USAGE
        assert run(["spec", "trace", "--spec", "specs/a.md", "--tests", ".",
                    "--id-pattern", "("]) == EXIT_USAGE

    def test_contracts(self, tmp_path: Path, capsys) -> None:
        (tmp_path / "old.json").write_text('{"properties": {"a": {}}}')
        (tmp_path / "new.json").write_text('{"properties": {}}')
        args = ["contracts", "diff", "--cwd", str(tmp_path), "--old", "old.json"]
        assert run([*args, "--new", "new.json"]) == EXIT_FAIL
        assert run([*args, "--new", "missing.json"]) == EXIT_USAGE
        manifest = tmp_path / "contracts.json"
        assert run(["contracts", "check", "--manifest", str(manifest)]) == EXIT_USAGE
        manifest.write_text('{"repos": {}, "contracts": []}')
        assert run(["contracts", "check", "--manifest", str(manifest),
                    "--checkouts", str(tmp_path)]) == EXIT_PASS
        manifest.write_text("{")
        assert run(["contracts", "check", "--manifest", str(manifest)]) == EXIT_USAGE


class TestPolicyCommands:
    def test_check(self, tmp_path: Path, capsys) -> None:
        root = ["--root", str(tmp_path)]
        assert run(["policy", "check", "--command", "ls", *root]) == EXIT_USAGE
        (tmp_path / ".quality-router").mkdir()
        policy = tmp_path / ".quality-router/policy.json"
        policy.write_text("{")
        assert run(["policy", "check", "--path", "a", *root]) == EXIT_USAGE
        policy.write_text(json.dumps({"deny_paths": ["**/.env"]}))
        assert run(["policy", "check", "--path", "x/.env", *root]) == EXIT_FAIL
        assert "denied_deny_paths" in capsys.readouterr().out
        assert run(["policy", "check", "--command", "ls", *root, "--json"]) == EXIT_PASS
        assert json.loads(capsys.readouterr().out)["summary"]["decision"] == "allow"

    def test_hook_no_policy_is_disconnected_noop(self, tmp_path, monkeypatch, capsys) -> None:
        stdin(monkeypatch, json.dumps({"command": "git push -f", "cwd": str(tmp_path)}))
        assert run(["policy", "hook", "--host", "cursor"]) == 0
        assert json.loads(capsys.readouterr().out) == {"permission": "allow"}

    def test_hook_denies_and_audits(self, tmp_path, monkeypatch, capsys) -> None:
        (tmp_path / "svc").mkdir()
        monkeypatch.chdir(tmp_path)
        assert run(["init", "--policy"]) == 0
        audit = tmp_path / "audit.jsonl"
        payload = {"tool_name": "Bash", "tool_input": {"command": "git push origin main"},
                   "cwd": str(tmp_path / "svc")}
        stdin(monkeypatch, json.dumps(payload))
        assert run(["policy", "hook", "--host", "claude-code", "--audit", str(audit)]) == 2
        assert "protected branch" in capsys.readouterr().err
        assert json.loads(audit.read_text())["rule"] == "protected_branches"

    def test_hook_explicit_policy_outside_qr_dir(self, tmp_path, monkeypatch, capsys) -> None:
        custom = tmp_path / "team-policy.json"
        custom.write_text(json.dumps({"deny_paths": ["**/*.pem"]}))
        stdin(monkeypatch, json.dumps({"file_path": "certs/a.pem"}))
        assert run(["policy", "hook", "--host", "cursor", "--policy", str(custom)]) == 0
        assert json.loads(capsys.readouterr().out)["permission"] == "deny"

    @pytest.mark.parametrize("raw", ["{", "[1]"])
    def test_hook_fails_closed(self, raw, tmp_path, monkeypatch, capsys) -> None:
        (tmp_path / ".quality-router").mkdir()
        (tmp_path / ".quality-router/policy.json").write_text("{}")
        monkeypatch.chdir(tmp_path)
        stdin(monkeypatch, raw)
        assert run(["policy", "hook", "--host", "claude-code"]) == 2
        assert "failed closed" in capsys.readouterr().err

    def test_hook_ignores_unrelated_tool_input(self, tmp_path, monkeypatch) -> None:
        (tmp_path / ".quality-router").mkdir()
        (tmp_path / ".quality-router/policy.json").write_text("{}")
        monkeypatch.chdir(tmp_path)
        stdin(monkeypatch, '{"tool_name": "Bash", "tool_input": 3}')
        assert run(["policy", "hook", "--host", "claude-code"]) == 0

    def test_hook_bad_policy_fails_closed(self, tmp_path, monkeypatch, capsys) -> None:
        (tmp_path / ".quality-router").mkdir()
        (tmp_path / ".quality-router/policy.json").write_text('{"deny_commands": [{}]}')
        monkeypatch.chdir(tmp_path)
        stdin(monkeypatch, "")
        assert run(["policy", "hook", "--host", "cursor"]) == 0
        assert json.loads(capsys.readouterr().out)["permission"] == "deny"


class TestEvalCommands:
    def test_prepare(self, java_repo, tmp_path: Path, capsys) -> None:
        repo, base = java_repo
        out = tmp_path / "task"
        common = ["eval", "prepare", "--repo", str(repo), "--base", "HEAD", "--task-id", "T-1",
                  "--out", str(out), "--hidden", "src/test/java/com/acme/LoaderTest.java"]
        assert run([*common, "--dry-run"]) == EXIT_PASS
        assert "dry_run=" in capsys.readouterr().out and not out.exists()
        assert run(common) == EXIT_PASS
        assert f"workspace={out / 'workspace'}" in capsys.readouterr().out
        assert run(common) == EXIT_FAIL
        assert run(["eval", "prepare", "--repo", str(tmp_path), "--base", base, "--task-id",
                    "x", "--out", str(tmp_path / "o")]) == EXIT_USAGE

    def test_report(self, tmp_path: Path, capsys) -> None:
        runs = tmp_path / "runs.jsonl"
        assert run(["eval", "report", "--runs", str(runs)]) == EXIT_USAGE
        runs.write_text("")
        assert run(["eval", "report", "--runs", str(runs)]) == EXIT_USAGE
        runs.write_text("{bad\n")
        assert run(["eval", "report", "--runs", str(runs)]) == EXIT_USAGE
        runs.write_text(json.dumps({"task": "a", "host": "h", "model": "m",
                                    "resolved": True}) + "\n")
        assert run(["eval", "report", "--runs", str(runs), "--json"]) == EXIT_PASS


class TestInitStamps:
    @pytest.mark.parametrize("host,hook_file", [("cursor", ".cursor/hooks.json"),
                                                ("claude-code", ".claude/settings.json")])
    def test_policy_with_host_hooks(self, host, hook_file, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        assert run(["init", "--host", host, "--policy"]) == 0
        assert (tmp_path / ".quality-router/policy.json").is_file()
        assert "qr policy hook" in (tmp_path / hook_file).read_text()
        assert not (tmp_path / ".cursor/mcp.json").exists()

    def test_policy_without_host_stamps_no_hooks(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        assert run(["init", "--policy", "--host", "vscode"]) == 0
        assert not (tmp_path / ".cursor/hooks.json").exists()
        assert not (tmp_path / ".claude").exists()

    def test_ci_template_never_overwrites(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        assert run(["init", "--ci", "github-maven"]) == 0
        workflow = tmp_path / GITHUB_MAVEN_PATH
        text = workflow.read_text()
        assert "mvn -B verify" in text and "qr gate diff-coverage" in text
        workflow.write_text("custom\n")
        assert stamp_ci(tmp_path, "github-maven") is False
        assert workflow.read_text() == "custom\n"

    def test_help_lists_harness_commands(self, capsys) -> None:
        with pytest.raises(SystemExit):
            run(["--help"])
        out = capsys.readouterr().out
        for command in ("gate", "lint", "spec", "contracts", "policy", "eval"):
            assert command in out
