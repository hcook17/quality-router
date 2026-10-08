"""Phase 7 held-out acceptance tests (specs/phase-7-roles-holdout.md AC-7.8..AC-7.12): the
lock records them by hash, the policy hides them from every role but test-author,
`qr gate holdout` checks they ran unmodified and passed, existing locks and gates behave as
before, and help shows the new options."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from typing import Any

import pytest

from harness.helpers import git
from quality_router.cli import run
from quality_router.harness.acceptance import LOCK_PATH, build_lock, load_lock
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
VISIBLE = "src/test/java/com/acme/ItemAcceptanceTest.java"
VISIBLE_SRC = """\
package com.acme;
class ItemAcceptanceTest {
    @Test @Tag("AC-1") void ac_1() {}
    @Test @Tag("AC-2") void ac_2() {}
}
"""
HOLDOUT = "holdout/ItemHoldoutTest.java"
HOLDOUT_SRC = """\
package com.acme;
class ItemHoldoutTest {
    @Test @Tag("AC-1") void trimsLongTitle() {}
    @Test @Tag("AC-1") void trimsTabs() {}
}
"""
HOLDOUT_CLASS = "com.acme.ItemHoldoutTest"
PASSING = [(HOLDOUT_CLASS, "trimsLongTitle", "pass"), (HOLDOUT_CLASS, "trimsTabs", "pass")]
REPORTS = "target/surefire-reports/*.xml"
POLICY = {"version": 1, "deny_paths": ["**/.env"], "roles": {
    "test-author": {"write_allow": ["**/src/test/**", "specs/**", "holdout/**"]},
    "implementer": {},
    "reviewer": {"write_allow": []},
}}
OUTCOMES = {
    "pass": "",
    "fail": '<failure message="expected: &lt;Intro&gt; but was: &lt;x&gt;">trace</failure>',
    "error": '<error message="boom" type="java.lang.IllegalStateException">trace</error>',
    "skip": "<skipped/>",
}


@pytest.fixture(autouse=True)
def no_role_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QR_ROLE", raising=False)


def put(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def commit(root: Path, message: str) -> str:
    git(root, "add", "-A")
    git(root, "commit", "-qm", message)
    return git(root, "rev-parse", "HEAD")


def track(root: Path, rel: str, message: str) -> str:
    git(root, "add", "-f", rel)
    git(root, "commit", "-qm", message)
    return git(root, "rev-parse", "HEAD")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed(root: Path) -> None:
    put(root, "contracts/item.schema.json", "{}")
    put(root, "specs/item.md", SPEC)
    put(root, VISIBLE, VISIBLE_SRC)
    put(root, ".quality-router/policy.json", json.dumps(POLICY, indent=2))


@pytest.fixture
def svc(repo: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Git checkout (also the cwd): spec, visible test and policy committed; the holdout file
    present but untracked (git-excluded)."""
    (repo / ".git/info").mkdir(parents=True, exist_ok=True)
    (repo / ".git/info/exclude").write_text("holdout/\ntarget/\n")
    seed(repo)
    commit(repo, "base")
    put(repo, HOLDOUT, HOLDOUT_SRC)
    monkeypatch.chdir(repo)
    return repo


def spec_lock(*extra: str) -> int:
    return run(["spec", "lock", "--spec", "specs/item.md", "--tests", VISIBLE, *extra])


@pytest.fixture
def locked(svc: Path) -> Path:
    """`svc` with a lock that records the holdout file, committed without the holdout file."""
    assert spec_lock("--holdout", HOLDOUT) == EXIT_PASS
    commit(svc, "spec: lock")
    return svc


def junit(root: Path, name: str, cases: list[tuple[str, str, str]]) -> Path:
    """Surefire-style report; each case is (classname, method, pass|fail|error|skip)."""
    count = {k: sum(1 for *_, outcome in cases if outcome == k) for k in OUTCOMES}
    rows = "".join(f'  <testcase classname="{c}" name="{m}">{OUTCOMES[o]}</testcase>\n'
                   for c, m, o in cases)
    text = (f'<testsuite name="{name}" tests="{len(cases)}" failures="{count["fail"]}" '
            f'errors="{count["error"]}" skipped="{count["skip"]}">\n{rows}</testsuite>\n')
    return put(root, f"target/surefire-reports/TEST-{name}.xml", text)


def gate(capsys: pytest.CaptureFixture[str], *extra: str) -> tuple[int, dict[str, Any]]:
    capsys.readouterr()
    code = run(["gate", "holdout", "--reports", REPORTS, "--json", *extra])
    return code, json.loads(capsys.readouterr().out)


def codes(payload: dict[str, Any], level: str = "error") -> list[str]:
    return sorted({f["code"] for f in payload["findings"] if f["level"] == level})


def stdin(monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any]) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))


class TestHoldoutLock:
    """AC-7.8 `qr spec lock --holdout` records held-out tests by hash and criteria; each must
    exist, not be a --tests file, and not be tracked by git."""

    def test_records_untracked_holdout(self, svc: Path) -> None:
        assert spec_lock("--holdout", HOLDOUT) == EXIT_PASS
        lock = json.loads((svc / LOCK_PATH).read_text())
        assert set(lock["holdout"]) == {HOLDOUT}
        assert lock["holdout"][HOLDOUT]["sha256"] == sha256(svc / HOLDOUT)
        assert lock["holdout"][HOLDOUT]["criteria"] == ["AC-1"]
        assert set(lock["tests"]) == {VISIBLE}

    @pytest.mark.parametrize("case", ["missing", "tracked", "also-tests"])
    def test_rejected(self, svc: Path, case: str) -> None:
        holdout, tests = HOLDOUT, [VISIBLE]
        if case == "missing":
            holdout = "holdout/NoSuchHoldoutTest.java"
        elif case == "tracked":
            track(svc, HOLDOUT, "holdout committed by mistake")
        else:
            tests.append(HOLDOUT)
        argv = ["spec", "lock", "--spec", "specs/item.md", "--tests", *tests, "--holdout", holdout]
        assert run(argv) == EXIT_USAGE
        assert not (svc / LOCK_PATH).exists()

    def test_without_holdout_no_key(self, svc: Path) -> None:
        assert spec_lock() == EXIT_PASS
        assert "holdout" not in json.loads((svc / LOCK_PATH).read_text())

    def test_root_not_a_git_work_tree_counts_as_untracked(self, tmp_path: Path,
                                                         monkeypatch: pytest.MonkeyPatch) -> None:
        plain = tmp_path / "plain"
        seed(plain)
        put(plain, HOLDOUT, HOLDOUT_SRC)
        monkeypatch.chdir(plain)
        assert spec_lock("--holdout", HOLDOUT) == EXIT_PASS
        assert json.loads((plain / LOCK_PATH).read_text())["holdout"][HOLDOUT]["criteria"] \
            == ["AC-1"]

    def test_build_lock(self, svc: Path) -> None:
        spec, test = [svc / "specs/item.md"], [svc / VISIBLE]
        lock = build_lock(svc, spec, test, None, holdout=[svc / HOLDOUT])
        assert lock["holdout"][HOLDOUT]["sha256"] == sha256(svc / HOLDOUT)
        assert lock["holdout"][HOLDOUT]["criteria"] == ["AC-1"]
        assert "holdout" not in build_lock(svc, spec, test, None)


class TestHoldoutHidden:
    """AC-7.9 Held-out tests are hidden from every role but test-author: reads, writes and shell
    commands naming them are denied with rule `holdout`."""

    @pytest.mark.parametrize("role,argv,code,denied", [
        (None, ["--path", HOLDOUT], EXIT_FAIL, ["denied_holdout"]),
        ("implementer", ["--command", f"grep -n assert {HOLDOUT}"], EXIT_FAIL,
         ["denied_holdout"]),
        ("test-author", ["--path", HOLDOUT], EXIT_PASS, []),
        ("implementer", ["--path", VISIBLE], EXIT_PASS, []),
    ], ids=["no-role-read", "implementer-grep", "test-author-read", "implementer-visible"])
    def test_policy_check(self, locked: Path, capsys: pytest.CaptureFixture[str],
                          role: str | None, argv: list[str], code: int,
                          denied: list[str]) -> None:
        capsys.readouterr()
        assert run(["policy", "check", *(["--role", role] if role else []), *argv,
                    "--json"]) == code
        payload = json.loads(capsys.readouterr().out)
        assert [f["code"] for f in payload["findings"] if f["level"] == "error"] == denied

    def test_hook(self, locked: Path, monkeypatch: pytest.MonkeyPatch,
                  capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
        audit = tmp_path / "audit.jsonl"
        hook = ["policy", "hook", "--host", "claude-code", "--audit", str(audit)]
        read = {"tool_name": "Read", "tool_input": {"file_path": HOLDOUT}, "cwd": str(locked)}
        stdin(monkeypatch, read)
        assert run(hook) == 2
        assert json.loads(audit.read_text().splitlines()[-1])["rule"] == "holdout"
        monkeypatch.setenv("QR_ROLE", "implementer")
        stdin(monkeypatch, {"tool_name": "Bash", "cwd": str(locked),
                            "tool_input": {"command": f"grep -n assert {HOLDOUT}"}})
        assert run(hook) == 2
        assert json.loads(audit.read_text().splitlines()[-1])["rule"] == "holdout"
        stdin(monkeypatch, {**read, "tool_input": {"file_path": VISIBLE}})
        assert run(hook) == 0
        monkeypatch.setenv("QR_ROLE", "test-author")
        stdin(monkeypatch, read)
        assert run(hook) == 0
        monkeypatch.delenv("QR_ROLE")
        stdin(monkeypatch, {"file_path": str(locked / HOLDOUT), "content": "",
                            "workspace_roots": [str(locked)]})
        capsys.readouterr()
        assert run(["policy", "hook", "--host", "cursor"]) == 0
        assert json.loads(capsys.readouterr().out)["permission"] == "deny"


class TestGateHoldout:
    """AC-7.10 `qr gate holdout` checks held-out tests ran unmodified and passed."""

    def test_all_ran_and_passed(self, locked: Path, capsys: pytest.CaptureFixture[str]) -> None:
        junit(locked, HOLDOUT_CLASS, PASSING)
        code, payload = gate(capsys)
        assert code == EXIT_PASS and payload["gate"] == "holdout"
        assert payload["findings"] == []
        assert payload["summary"] == {"holdout_files": 1, "holdout_tests": 2,
                                      "holdout_failed": 0, "holdout_skipped": 0,
                                      "criteria": ["AC-1"], "reports": 1}

    def test_text_summary(self, locked: Path, capsys: pytest.CaptureFixture[str]) -> None:
        junit(locked, HOLDOUT_CLASS, PASSING)
        capsys.readouterr()
        assert run(["gate", "holdout", "--reports", REPORTS]) == EXIT_PASS
        lines = capsys.readouterr().out.splitlines()
        for line in ("holdout_files=1", "holdout_tests=2", "holdout_failed=0",
                     "holdout_skipped=0", 'criteria=["AC-1"]', "reports=1"):
            assert line in lines

    def test_gate_holdout_module(self, locked: Path) -> None:
        from quality_router.harness.acceptance import gate_holdout

        report = junit(locked, HOLDOUT_CLASS, PASSING)
        result = gate_holdout(locked, [report])
        assert result.gate == "holdout" and result.passed and result.findings == []
        assert result.summary["holdout_tests"] == 2

    @pytest.mark.parametrize("state", ["no-lock", "no-holdout-key"])
    def test_no_holdout(self, svc: Path, capsys: pytest.CaptureFixture[str], state: str) -> None:
        if state == "no-holdout-key":
            assert spec_lock() == EXIT_PASS
        junit(svc, HOLDOUT_CLASS, PASSING)
        code, payload = gate(capsys)
        assert code == EXIT_PASS and codes(payload, "warning") == ["no_holdout"]
        code, payload = gate(capsys, "--strict")
        assert code == EXIT_FAIL and codes(payload, "warning") == ["no_holdout"]

    def test_reports_match_nothing(self, locked: Path, capsys: pytest.CaptureFixture[str]) -> None:
        capsys.readouterr()
        assert run(["gate", "holdout", "--reports", "target/nothing/*.xml"]) == EXIT_USAGE
        assert "Error: JUnit report not found" in capsys.readouterr().err

    def test_missing(self, locked: Path, capsys: pytest.CaptureFixture[str]) -> None:
        junit(locked, HOLDOUT_CLASS, PASSING)
        (locked / HOLDOUT).unlink()
        code, payload = gate(capsys)
        assert (code, codes(payload)) == (EXIT_FAIL, ["holdout_missing"])

    def test_modified(self, locked: Path, capsys: pytest.CaptureFixture[str]) -> None:
        junit(locked, HOLDOUT_CLASS, PASSING)
        (locked / HOLDOUT).write_text(HOLDOUT_SRC.replace("trimsTabs", "trimsSpaces"))
        code, payload = gate(capsys)
        assert (code, codes(payload)) == (EXIT_FAIL, ["holdout_modified"])

    def test_tracked(self, locked: Path, capsys: pytest.CaptureFixture[str]) -> None:
        junit(locked, HOLDOUT_CLASS, PASSING)
        track(locked, HOLDOUT, "leak")
        code, payload = gate(capsys)
        assert (code, codes(payload)) == (EXIT_FAIL, ["holdout_exposed"])

    def test_touched_in_base_range(self, locked: Path,
                                   capsys: pytest.CaptureFixture[str]) -> None:
        junit(locked, HOLDOUT_CLASS, PASSING)
        base = git(locked, "rev-parse", "HEAD")
        assert gate(capsys, "--base", "HEAD~1")[0] == EXIT_PASS
        track(locked, HOLDOUT, "leak")
        git(locked, "rm", "-q", "--cached", HOLDOUT)
        git(locked, "commit", "-qm", "unleak")
        assert (locked / HOLDOUT).read_text() == HOLDOUT_SRC
        code, payload = gate(capsys, "--base", base)
        assert (code, codes(payload)) == (EXIT_FAIL, ["holdout_exposed"])

    @pytest.mark.parametrize("cases", [
        [("com.acme.ItemAcceptanceTest", "ac_1", "pass")],
        [(HOLDOUT_CLASS, "trimsLongTitle", "skip"), (HOLDOUT_CLASS, "trimsTabs", "skip")],
    ], ids=["no-testcase", "all-skipped"])
    def test_not_run(self, locked: Path, capsys: pytest.CaptureFixture[str],
                     cases: list[tuple[str, str, str]]) -> None:
        junit(locked, "run", cases)
        code, payload = gate(capsys)
        assert (code, codes(payload)) == (EXIT_FAIL, ["holdout_not_run"])

    def test_failed_names_methods(self, locked: Path, capsys: pytest.CaptureFixture[str]) -> None:
        junit(locked, HOLDOUT_CLASS, [(HOLDOUT_CLASS, "trimsLongTitle", "fail"),
                                      (HOLDOUT_CLASS, "trimsTabs", "error"),
                                      (HOLDOUT_CLASS, "keepsInnerSpace", "pass")])
        code, payload = gate(capsys)
        assert (code, codes(payload)) == (EXIT_FAIL, ["holdout_failed"])
        named = " ".join(f"{f['path']} {f['message']}" for f in payload["findings"]
                         if f["code"] == "holdout_failed")
        assert "trimsLongTitle" in named and "trimsTabs" in named

    @pytest.mark.parametrize("classname,matches", [
        ("ItemHoldoutTest", True),
        ("com.acme.ItemHoldoutTest$Nested", True),
        ("com.acme.ItemHoldoutTestHelper", False),
    ])
    def test_classname_matching(self, locked: Path, capsys: pytest.CaptureFixture[str],
                                classname: str, matches: bool) -> None:
        junit(locked, "mixed", [*PASSING, (classname, "extra", "fail")])
        code, payload = gate(capsys)
        expected = (EXIT_FAIL, ["holdout_failed"]) if matches else (EXIT_PASS, [])
        assert (code, codes(payload)) == expected


class TestExistingLocksAndGates:
    """AC-7.11 `qr gate acceptance` ignores the holdout key and needs no holdout files; locks
    without `holdout` load and protect files as before."""

    def test_gate_acceptance_with_holdout_absent(self, locked: Path,
                                                 capsys: pytest.CaptureFixture[str]) -> None:
        (locked / HOLDOUT).unlink()
        capsys.readouterr()
        assert run(["gate", "acceptance", "--json"]) == EXIT_PASS
        assert json.loads(capsys.readouterr().out)["passed"] is True

    def test_lock_without_holdout(self, svc: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert spec_lock() == EXIT_PASS
        commit(svc, "spec: lock")
        assert "holdout" not in load_lock(svc / LOCK_PATH)
        assert run(["gate", "acceptance"]) == EXIT_PASS
        capsys.readouterr()
        assert run(["policy", "check", "--write", "--path", VISIBLE]) == EXIT_FAIL
        assert "denied_acceptance_lock" in capsys.readouterr().out

    def test_holdout_lock_still_protects_visible_files(
            self, locked: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert set(load_lock(locked / LOCK_PATH)["tests"]) == {VISIBLE}
        capsys.readouterr()
        assert run(["policy", "check", "--write", "--path", VISIBLE]) == EXIT_FAIL
        assert "denied_acceptance_lock" in capsys.readouterr().out
        assert run(["policy", "check", "--path", VISIBLE]) == EXIT_PASS


class TestHelp:
    """AC-7.12 Help shows the new options."""

    @pytest.mark.parametrize("argv,needle", [
        (["gate", "holdout", "--help"], "--reports"),
        (["policy", "check", "--help"], "--role"),
        (["spec", "lock", "--help"], "--holdout"),
        (["gate", "--help"], "qr gate holdout"),
    ])
    def test_help(self, capsys: pytest.CaptureFixture[str], argv: list[str],
                  needle: str) -> None:
        with pytest.raises(SystemExit) as exc:
            run(argv)
        assert exc.value.code == 0
        assert needle in capsys.readouterr().out
