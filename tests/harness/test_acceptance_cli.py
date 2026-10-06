"""End-to-end `qr` argv for the acceptance-first commands: spec new/lint/scaffold/lock,
gate acceptance, feedback junit, and lock-aware policy check/hook."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from harness.helpers import git
from quality_router.cli import run
from quality_router.harness.acceptance import LOCK_PATH
from quality_router.harness.ci import GITHUB_MAVEN
from quality_router.harness.report import EXIT_FAIL, EXIT_PASS, EXIT_USAGE

SPEC = """\
# Item
Contract: `contracts/item.schema.json`
### AC-1 Title is trimmed
| title | expected title |
| --- | --- |
| `  Intro ` | Intro |
### AC-2 Licence
| manifest | expected licenseId |
| --- | --- |
| (null) | UNLICENSED |
"""
OUT = "src/test/java/demo/ItemAcceptanceTest.java"
REPORT = """\
<testsuite>
  <testcase name="ac_2(String, String)[1]" classname="demo.ItemAcceptanceTest">
    <failure message="expected: &lt;UNLICENSED&gt; but was: &lt;null&gt;" type="X">t</failure>
  </testcase>
</testsuite>
"""


def stdin(monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(text))


def commit(root: Path, message: str) -> None:
    git(root, "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@x", "commit", "-qm", message)


@pytest.fixture
def svc(repo: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(repo)
    (repo / "contracts").mkdir()
    (repo / "contracts/item.schema.json").write_text("{}")
    (repo / "specs").mkdir()
    (repo / "specs/item.md").write_text(SPEC)
    commit(repo, "base")
    return repo


def scaffold(*extra: str) -> int:
    return run(["spec", "scaffold", "--spec", "specs/item.md", "--package", "demo",
                "--bind", "AC-1=svc.title(title)", "--out", OUT, *extra])


class TestSpecCommands:
    def test_new_then_lint(self, tmp_path: Path, monkeypatch, capsys) -> None:
        monkeypatch.chdir(tmp_path)
        assert run(["spec", "new", "--title", "Item v2", "--out", "s.md", "--dry-run"]) == 0
        assert "# Item v2" in capsys.readouterr().out and not (tmp_path / "s.md").exists()
        assert run(["spec", "new", "--title", "Item v2", "--out", "specs/s.md",
                    "--contract", "c.json"]) == EXIT_PASS
        assert run(["spec", "new", "--title", "x", "--out", "specs/s.md"]) == EXIT_USAGE
        (tmp_path / "c.json").write_text("{}")
        assert run(["spec", "lint", "--spec", "specs/*.md", "--root", str(tmp_path)]) == 0
        capsys.readouterr()
        assert run(["spec", "lint", "--spec", "specs/s.md", "--json"]) == EXIT_PASS
        assert json.loads(capsys.readouterr().out)["summary"]["criteria"] == 2

    def test_lint_usage_and_failure(self, tmp_path: Path, monkeypatch, capsys) -> None:
        monkeypatch.chdir(tmp_path)
        assert run(["spec", "lint", "--spec", "nope.md"]) == EXIT_USAGE
        (tmp_path / "d.md").write_text("- AC-1 handle errors gracefully\n")
        assert run(["spec", "lint", "--spec", "d.md", "--id-pattern", "("]) == EXIT_USAGE
        assert run(["spec", "lint", "--spec", "d.md"]) == EXIT_FAIL
        assert "criterion_without_examples" in capsys.readouterr().out

    def test_scaffold(self, svc: Path, capsys) -> None:
        assert scaffold("--dry-run") == EXIT_PASS
        assert "class ItemAcceptanceTest {" in capsys.readouterr().out
        assert not (svc / OUT).exists()
        assert scaffold() == EXIT_PASS
        out = capsys.readouterr().out
        assert "criteria=AC-1,AC-2" in out and "unbound=AC-2" in out
        assert '@Tag("AC-2")' in (svc / OUT).read_text()
        assert scaffold() == EXIT_USAGE
        assert scaffold("--force", "--ac", "AC-1") == EXIT_PASS
        assert "unbound" not in capsys.readouterr().out

    def test_scaffold_java_release_from_build_and_spring(self, svc: Path, capsys) -> None:
        (svc / "pom.xml").write_text("<project><properties><java.version>11</java.version>"
                                     "</properties></project>")
        assert scaffold("--spring-boot-test", "--field", "@Autowired Svc svc",
                        "--import", "demo.app.Svc") == EXIT_PASS
        out = capsys.readouterr().out
        assert "java_release=11  # from " in out and "pom.xml" in out
        src = (svc / OUT).read_text()
        assert "value = {" in src and "textBlock" not in src
        assert "@SpringBootTest\nclass ItemAcceptanceTest" in src
        assert "    @Autowired Svc svc;" in src and "import demo.app.Svc;" in src
        assert scaffold("--force", "--java-release", "21",
                        "--class-annotation", '@ActiveProfiles("test")') == EXIT_PASS
        assert "java_release=21  # --java-release" in capsys.readouterr().out
        src = (svc / OUT).read_text()
        assert 'textBlock = """' in src and '@ActiveProfiles("test")\nclass' in src

    def test_scaffold_java_release_default(self, svc: Path, capsys) -> None:
        assert scaffold() == EXIT_PASS
        assert "java_release=17  # default" in capsys.readouterr().out

    @pytest.mark.parametrize("extra", [
        ["--bind", "AC-1"], ["--class", "1Bad"], ["--ac", "AC-9"], ["--id-pattern", "("],
        ["--java-release", "7"], ["--class-annotation", "NoAt"], ["--import", "a b"],
    ])
    def test_scaffold_usage(self, svc: Path, extra: list[str]) -> None:
        assert scaffold(*extra) == EXIT_USAGE

    def test_scaffold_refuses_unlinted_spec(self, svc: Path, capsys) -> None:
        assert run(["spec", "scaffold", "--spec", "missing.md", "--out", OUT]) == EXIT_USAGE
        (svc / "specs/bad.md").write_text("- AC-1 vague\n")
        assert run(["spec", "scaffold", "--spec", "specs/bad.md", "--out", OUT]) == EXIT_FAIL
        assert "does not lint clean" in capsys.readouterr().err

    def test_lock_flow(self, svc: Path, capsys) -> None:
        lock = ["spec", "lock", "--spec", "specs/item.md", "--tests", "src/test/java/**/*.java"]
        assert run(lock) == EXIT_USAGE
        assert scaffold() == EXIT_PASS
        assert run([*lock, "--dry-run"]) == EXIT_PASS
        assert '"owned"' in capsys.readouterr().out and not (svc / LOCK_PATH).exists()
        assert run([*lock, "--ac", "AC-7"]) == EXIT_USAGE
        assert run([*lock, "--id-pattern", "("]) == EXIT_USAGE
        assert run(["spec", "lock", "--spec", "x.md", "--tests", OUT]) == EXIT_USAGE
        assert run([*lock, "--approved-by", "qa-lead"]) == EXIT_PASS
        assert "owned=AC-1,AC-2" in capsys.readouterr().out
        assert json.loads((svc / LOCK_PATH).read_text())["approved_by"] == "qa-lead"
        (svc / "specs/item.md").write_text("- AC-1 TBD\n")
        assert run(lock) == EXIT_FAIL
        assert "refusing to lock" in capsys.readouterr().err


class TestGateAndPolicy:
    @pytest.fixture
    def locked(self, svc: Path) -> Path:
        assert scaffold() == EXIT_PASS
        assert run(["spec", "lock", "--spec", "specs/item.md", "--tests", OUT]) == EXIT_PASS
        commit(svc, "spec: lock")
        return svc

    def test_gate(self, locked: Path, tmp_path: Path, capsys) -> None:
        assert run(["gate", "acceptance"]) == EXIT_PASS
        capsys.readouterr()
        assert run(["gate", "acceptance", "--base", "HEAD~1", "--json"]) == EXIT_PASS
        assert json.loads(capsys.readouterr().out)["summary"]["owned"] == ["AC-1", "AC-2"]
        assert run(["gate", "acceptance", "--base", "nope"]) == EXIT_USAGE
        assert run(["gate", "acceptance", "--root", str(tmp_path / "x")]) == EXIT_USAGE
        (locked / OUT).write_text("weakened\n")
        assert run(["gate", "acceptance"]) == EXIT_FAIL
        assert "locked_test_modified" in capsys.readouterr().out
        (locked / LOCK_PATH).write_text("{")
        assert run(["gate", "acceptance"]) == EXIT_USAGE

    def test_policy_check_write(self, locked: Path, capsys) -> None:
        assert run(["init", "--policy"]) == 0
        assert run(["policy", "check", "--path", OUT]) == EXIT_PASS
        assert run(["policy", "check", "--write", "--path", OUT]) == EXIT_FAIL
        assert "denied_acceptance_lock" in capsys.readouterr().out
        assert run(["policy", "check", "--command", "qr spec lock --spec s"]) == EXIT_FAIL
        (locked / LOCK_PATH).write_text("{")
        assert run(["policy", "check", "--path", OUT]) == EXIT_USAGE

    def test_hook_enforces_lock_without_policy(self, locked: Path, monkeypatch, capsys) -> None:
        edit = {"tool_name": "Edit", "tool_input": {"file_path": str(locked / OUT)},
                "cwd": str(locked)}
        stdin(monkeypatch, json.dumps(edit))
        assert run(["policy", "hook", "--host", "claude-code"]) == 2
        assert "approved acceptance file" in capsys.readouterr().err
        stdin(monkeypatch, json.dumps({**edit, "tool_name": "Read"}))
        assert run(["policy", "hook", "--host", "claude-code"]) == 0
        assert run(["init", "--policy"]) == 0
        stdin(monkeypatch, json.dumps({"tool_name": "Write", "tool_input": {
            "file_path": LOCK_PATH}, "workspace_roots": [str(locked)]}))
        assert run(["policy", "hook", "--host", "cursor"]) == 0
        assert json.loads(capsys.readouterr().out)["permission"] == "deny"
        (locked / LOCK_PATH).write_text("{")
        stdin(monkeypatch, json.dumps(edit))
        assert run(["policy", "hook", "--host", "claude-code"]) == 2
        assert "failed closed" in capsys.readouterr().err


class TestFeedback:
    def test_feedback_junit(self, svc: Path, capsys) -> None:
        assert scaffold() == EXIT_PASS
        reports = svc / "target/surefire-reports"
        reports.mkdir(parents=True)
        assert run(["feedback", "junit", "--reports", "target/surefire-reports/*.xml"]) \
            == EXIT_USAGE
        (reports / "TEST-ok.xml").write_text('<testsuite><testcase name="a"/></testsuite>')
        assert run(["feedback", "junit", "--reports", "target/surefire-reports/*.xml"]) \
            == EXIT_PASS
        (reports / "TEST-item.xml").write_text(REPORT)
        args = ["feedback", "junit", "--reports", "target/surefire-reports/*.xml",
                "--sources", "src/test/java", "--spec", "specs/item.md"]
        assert run(args) == EXIT_FAIL
        out = capsys.readouterr().out
        assert "FAIL AC-2 Licence [invocation 1]" in out
        assert "expected <UNLICENSED> but was <null>" in out
        assert run([*args, "--json"]) == EXIT_FAIL
        assert json.loads(capsys.readouterr().out)["failures"][0]["criteria"] == ["AC-2"]
        assert run([*args, "--spec", "nope.md"]) == EXIT_USAGE
        assert run([*args, "--id-pattern", "("]) == EXIT_USAGE
        (reports / "TEST-bad.xml").write_text("<testsuite>")
        assert run(args) == EXIT_USAGE


def test_ci_template_runs_acceptance_and_feedback() -> None:
    assert "qr gate acceptance --base" in GITHUB_MAVEN
    assert "qr feedback junit" in GITHUB_MAVEN
