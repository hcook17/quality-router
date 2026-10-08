"""Implementation edges of phase-7 roles and held-out tests not pinned by the locked set."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.helpers import git
from quality_router.cli import run
from quality_router.harness.policy import HookEvent, Policy, decide
from quality_router.harness.report import EXIT_USAGE

ROLES = {"test-author": {"write_allow": ["**/src/test/**"]},
         "implementer": {"read_deny": ["holdout/**"]}}


@pytest.fixture
def policy(tmp_path: Path) -> Policy:
    return Policy.from_dict({"roles": ROLES})


def as_role(policy: Policy, root: Path, role: str, command: str) -> str:
    decision = decide(HookEvent("command", command, str(root)), policy, root, role=role)
    return "allow" if decision.allow else decision.rule


@pytest.mark.parametrize("command,expected", [
    ("echo x > src/main/java/A.java", "role_write_allow"),
    ("echo x >> src/test/java/ATest.java", "allow"),
    ("./gradlew test; cp a.txt src/main/A.java", "role_write_allow"),
    ("FOO=1 ./tools/fmt.sh > src/test/out.txt", "allow"),
    ("sed -i 's/a/b/' src/test/java/ATest.java", "allow"),
    ("echo 'unbalanced > src/main/A.java", "role_write_allow"),
])
def test_test_author_shell_writes(policy: Policy, tmp_path: Path, command: str,
                                  expected: str) -> None:
    assert as_role(policy, tmp_path, "test-author", command) == expected


def test_read_deny_sees_program_paths(policy: Policy, tmp_path: Path) -> None:
    assert as_role(policy, tmp_path, "implementer", "./holdout/run.sh") == "role_read_deny"


@pytest.mark.parametrize("roles", [
    {"r": {"write_allow": "src/**"}},
    {"r": {"read_deny": "holdout/**"}},
    {"r": {"deny_commands": "git push"}},
])
def test_role_lists_must_be_lists(roles: dict) -> None:
    with pytest.raises(ValueError):
        Policy.from_dict({"roles": roles})


@pytest.fixture
def svc(repo: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (repo / "contracts").mkdir()
    (repo / "contracts/item.schema.json").write_text("{}")
    (repo / "specs").mkdir()
    (repo / "specs/item.md").write_text(
        "# Item\nContract: `contracts/item.schema.json`\n### AC-1 Title\n"
        "| title | expected title |\n| --- | --- |\n| a | a |\n")
    test = repo / "src/test/java/ItemAcceptanceTest.java"
    test.parent.mkdir(parents=True)
    test.write_text('class ItemAcceptanceTest { @Tag("AC-1") void a() {} }\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    holdout = repo / "holdout/ItemHoldoutTest.java"
    holdout.parent.mkdir()
    holdout.write_text('class ItemHoldoutTest { @Tag("AC-1") void b() {} }\n')
    monkeypatch.chdir(repo)
    return repo


def lock(*holdout: str) -> int:
    return run(["spec", "lock", "--spec", "specs/item.md", "--tests",
                "src/test/java/ItemAcceptanceTest.java", "--holdout", *holdout])


def test_holdout_glob_matching_nothing(svc: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert lock("holdout/*Missing*.java") == EXIT_USAGE
    assert "held-out test not found" in capsys.readouterr().err


def test_gate_bad_base_and_bad_xml(svc: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert lock("holdout/ItemHoldoutTest.java") == 0
    report = svc / "out/TEST-x.xml"
    report.parent.mkdir()
    report.write_text('<testsuite><testcase classname="ItemHoldoutTest" name="b"/></testsuite>')
    capsys.readouterr()
    assert run(["gate", "holdout", "--reports", "out/*.xml", "--base", "no-such-ref"]) \
        == EXIT_USAGE
    assert "cannot list commits" in capsys.readouterr().err
    report.write_text("<testsuite")
    assert run(["gate", "holdout", "--reports", "out/*.xml"]) == EXIT_USAGE
    assert "not JUnit XML" in capsys.readouterr().err


def test_lock_with_bad_holdout_entry_fails_closed(svc: Path) -> None:
    assert lock("holdout/ItemHoldoutTest.java") == 0
    path = svc / ".quality-router/acceptance.lock.json"
    data = json.loads(path.read_text())
    data["holdout"] = {"holdout/ItemHoldoutTest.java": "deadbeef"}
    path.write_text(json.dumps(data))
    assert run(["policy", "check", "--path", "README.md"]) == EXIT_USAGE
