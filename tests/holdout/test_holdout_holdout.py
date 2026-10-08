"""Held-out checks for phase 7 held-out tests (specs/phase-7-roles-holdout.md AC-8..AC-12).

Self-contained: pytest, the stdlib and quality_router only.
"""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from quality_router.cli import run

EXIT_PASS, EXIT_FAIL, EXIT_USAGE = 0, 1, 2
LOCK_FILE = ".quality-router/acceptance.lock.json"
SPEC_REL = "specs/catalog.md"
SPEC = """\
# Catalog price

Contract: `schemas/catalog.schema.json`

### AC-1 Price is rounded half-up to cents

| price | expected price |
| --- | --- |
| `1.005` | 1.01 |

### AC-2 Currency is EUR when absent

| currency | expected currency |
| --- | --- |
| (null) | EUR |

### AC-3 Tags are lower-cased

| tags | expected tags |
| --- | --- |
| `A,b` | a,b |
"""
VISIBLE = "src/test/java/com/acme/catalog/CatalogAcceptanceTest.java"
VISIBLE_SRC = """\
package com.acme.catalog;
class CatalogAcceptanceTest {
    @Test @Tag("AC-1") void ac_1() {}
    @Test @Tag("AC-2") void ac_2() {}
    @Test @Tag("AC-3") void ac_3() {}
}
"""
HOLD_A = "qa-holdout/CatalogHoldoutTest.java"
HOLD_A_SRC = """\
package com.acme.catalog;
// Varies scale and boundaries for AC-1 and AC-3.
class CatalogHoldoutTest {
    @Test @Tag("AC-1") void roundsHalfUp() {}
    @Test @Tag("AC-3") void lowercasesTags() {}
}
"""
HOLD_B = "qa-holdout/edge/CatalogEdgeHoldoutTest.java"
HOLD_B_SRC = """\
package com.acme.catalog;
class CatalogEdgeHoldoutTest {
    @Test @Tag("AC-2") void defaultsCurrency() {}
}
"""
HOLD_GLOB = "qa-holdout/**/*.java"
CLASS_A = "com.acme.catalog.CatalogHoldoutTest"
CLASS_B = "com.acme.catalog.CatalogEdgeHoldoutTest"
CLASS_VISIBLE = "com.acme.catalog.CatalogAcceptanceTest"
ALL_PASS = [(CLASS_A, "roundsHalfUp", "pass"), (CLASS_A, "lowercasesTags", "pass"),
            (CLASS_B, "defaultsCurrency", "pass")]
REPORTS = "build/test-results/**/*.xml"
SUMMARY_KEYS = {"holdout_files", "holdout_tests", "holdout_failed", "holdout_skipped",
                "criteria", "reports"}
POLICY = {"version": 1, "deny_paths": ["**/.env"], "roles": {
    "spec-author": {"write_allow": ["specs/**", "docs/**", "**/*.md"]},
    "test-author": {"write_allow": ["**/src/test/**", "specs/**", "qa-holdout/**"]},
    "implementer": {},
    "reviewer": {"write_allow": []},
}}
OUTCOMES = {
    "pass": "",
    "fail": '<failure message="expected: &lt;1.01&gt; but was: &lt;1.0&gt;" '
            'type="org.opentest4j.AssertionFailedError">at x</failure>',
    "error": '<error message="NPE" type="java.lang.NullPointerException">at y</error>',
    "skip": '<skipped message="disabled"/>',
}


@pytest.fixture(autouse=True)
def _clear_role_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QR_ROLE", raising=False)


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(cwd), "-c", "user.name=h", "-c", "user.email=h@localhost",
         "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false", *args],
        capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def _put(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _commit_all(root: Path, message: str) -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD")


def _force_commit(root: Path, rel: str, message: str) -> str:
    _git(root, "add", "-f", rel)
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed(root: Path) -> None:
    _put(root, "schemas/catalog.schema.json", '{"type": "object"}')
    _put(root, SPEC_REL, SPEC)
    _put(root, VISIBLE, VISIBLE_SRC)
    _put(root, ".quality-router/policy.json", json.dumps(POLICY, indent=2))


def _holdouts(root: Path) -> None:
    _put(root, HOLD_A, HOLD_A_SRC)
    _put(root, HOLD_B, HOLD_B_SRC)


@pytest.fixture
def cat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = (tmp_path / "catalog").resolve()
    root.mkdir()
    _git(root, "init", "-q")
    (root / ".git/info").mkdir(parents=True, exist_ok=True)
    (root / ".git/info/exclude").write_text("qa-holdout/\nbuild/\n")
    _seed(root)
    _commit_all(root, "base")
    _holdouts(root)
    monkeypatch.chdir(root)
    return root


def _lock(*extra: str) -> int:
    return run(["spec", "lock", "--spec", SPEC_REL, "--tests", VISIBLE, *extra])


@pytest.fixture
def cat_locked(cat: Path) -> Path:
    assert _lock("--holdout", HOLD_GLOB) == EXIT_PASS
    _commit_all(cat, "spec: lock catalog")
    return cat


def _read_lock(root: Path) -> dict[str, Any]:
    return json.loads((root / LOCK_FILE).read_text())


def _junit(root: Path, rel: str, cases: list[tuple[str, str, str]], wrap: bool = False) -> Path:
    count = {k: sum(1 for *_, o in cases if o == k) for k in OUTCOMES}
    rows = "\n".join(f'    <testcase name="{m}" classname="{c}" time="0.004">{OUTCOMES[o]}'
                     "</testcase>" for c, m, o in cases)
    suite = (f'  <testsuite name="{cases[0][0] if cases else "none"}" tests="{len(cases)}" '
             f'skipped="{count["skip"]}" failures="{count["fail"]}" errors="{count["error"]}" '
             'timestamp="2026-10-07T10:00:00" hostname="ci" time="0.1">\n'
             "    <properties/>\n"
             f"{rows}\n"
             "    <system-out><![CDATA[]]></system-out>\n"
             "    <system-err><![CDATA[]]></system-err>\n"
             "  </testsuite>")
    body = f"<testsuites>\n{suite}\n</testsuites>" if wrap else suite.strip()
    return _put(root, rel, '<?xml version="1.0" encoding="UTF-8"?>\n' + body + "\n")


def _report(root: Path, cases: list[tuple[str, str, str]], name: str = "all") -> Path:
    return _junit(root, f"build/test-results/test/TEST-{name}.xml", cases)


def _gate(capsys: pytest.CaptureFixture[str], *extra: str,
          reports: str = REPORTS) -> tuple[int, dict[str, Any]]:
    capsys.readouterr()
    code = run(["gate", "holdout", "--reports", reports, "--json", *extra])
    return code, json.loads(capsys.readouterr().out)


def _codes(payload: dict[str, Any], level: str = "error") -> list[str]:
    return sorted({f["code"] for f in payload["findings"] if f["level"] == level})


def _stdin(monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any]) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))


# --------------------------------------------------------------------------- #
# AC-8
# --------------------------------------------------------------------------- #

def test_ac8_glob_records_every_match(cat: Path) -> None:
    """AC-8: a holdout glob records each matching file with its sha256 and criteria."""
    assert _lock("--holdout", HOLD_GLOB) == EXIT_PASS
    holdout = _read_lock(cat)["holdout"]
    assert set(holdout) == {HOLD_A, HOLD_B}
    assert holdout[HOLD_A]["sha256"] == _sha(cat / HOLD_A)
    assert holdout[HOLD_B]["sha256"] == _sha(cat / HOLD_B)
    assert sorted(holdout[HOLD_A]["criteria"]) == ["AC-1", "AC-3"]
    assert holdout[HOLD_B]["criteria"] == ["AC-2"]


def test_ac8_absolute_path_recorded_relative(cat: Path) -> None:
    """AC-8: an absolute holdout path under --root is recorded relative to the root."""
    assert _lock("--root", str(cat), "--holdout", str(cat / HOLD_B)) == EXIT_PASS
    holdout = _read_lock(cat)["holdout"]
    assert set(holdout) == {HOLD_B}
    assert holdout[HOLD_B]["criteria"] == ["AC-2"]


def test_ac8_staged_file_counts_as_tracked(cat: Path) -> None:
    """AC-8: a holdout file added to the git index is tracked; the lock is refused."""
    _git(cat, "add", "-f", HOLD_A)
    assert _lock("--holdout", HOLD_A) == EXIT_USAGE
    assert not (cat / LOCK_FILE).exists()


def test_ac8_one_tracked_file_in_glob_refuses_all(cat: Path) -> None:
    """AC-8: if any file a holdout glob matches is tracked, nothing is written."""
    _force_commit(cat, HOLD_B, "edge holdout committed")
    assert _lock("--holdout", HOLD_GLOB) == EXIT_USAGE
    assert not (cat / LOCK_FILE).exists()


def test_ac8_holdout_also_matched_by_tests_glob(cat: Path) -> None:
    """AC-8: a holdout file that a --tests glob also matches is refused."""
    hidden = "src/test/java/com/acme/catalog/CatalogHiddenHoldoutTest.java"
    _put(cat, hidden, HOLD_A_SRC.replace("CatalogHoldoutTest", "CatalogHiddenHoldoutTest"))
    argv = ["spec", "lock", "--spec", SPEC_REL, "--tests", "src/test/java/**/*.java",
            "--holdout", hidden]
    assert run(argv) == EXIT_USAGE
    assert not (cat / LOCK_FILE).exists()


def test_ac8_refused_lock_leaves_existing_lock(cat: Path) -> None:
    """AC-8: a refused --holdout lock does not overwrite the lock already there."""
    assert _lock() == EXIT_PASS
    before = (cat / LOCK_FILE).read_bytes()
    assert "holdout" not in _read_lock(cat)
    assert _lock("--holdout", "qa-holdout/MissingHoldoutTest.java") == EXIT_USAGE
    assert (cat / LOCK_FILE).read_bytes() == before


def test_ac8_non_git_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-8: a root that is not a git work tree counts as untracked."""
    plain = tmp_path / "unversioned"
    _seed(plain)
    _holdouts(plain)
    monkeypatch.chdir(plain)
    assert _lock("--holdout", HOLD_A, "--approved-by", "spec-owner") == EXIT_PASS
    lock = _read_lock(plain)
    assert sorted(lock["holdout"][HOLD_A]["criteria"]) == ["AC-1", "AC-3"]
    assert lock["approved_by"] == "spec-owner"


def test_ac8_build_lock_module(cat: Path) -> None:
    """AC-8: build_lock(holdout=[...]) adds the map; holdout=None leaves no key."""
    from quality_router.harness.acceptance import build_lock

    specs, tests = [cat / SPEC_REL], [cat / VISIBLE]
    lock = build_lock(cat, specs, tests, None, holdout=[cat / HOLD_A, cat / HOLD_B])
    assert set(lock["holdout"]) == {HOLD_A, HOLD_B}
    assert lock["holdout"][HOLD_B]["sha256"] == _sha(cat / HOLD_B)
    assert set(lock["tests"]) == {VISIBLE}
    assert "holdout" not in build_lock(cat, specs, tests, None, holdout=None)


# --------------------------------------------------------------------------- #
# AC-9
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("role,argv,denied", [
    (None, ["--path", "<abs-a>"], ["denied_holdout"]),
    ("implementer", ["--path", HOLD_B], ["denied_holdout"]),
    ("reviewer", ["--path", HOLD_A], ["denied_holdout"]),
    ("spec-author", ["--path", HOLD_A], ["denied_holdout"]),
    ("implementer", ["--write", "--path", HOLD_A], ["denied_holdout"]),
    ("implementer", ["--command", f"cat ./{HOLD_A}"], ["denied_holdout"]),
    ("implementer", ["--command", "sed -n 1,20p <abs-b>"], ["denied_holdout"]),
    ("implementer", ["--command", f"wc -l < {HOLD_B}"], ["denied_holdout"]),
    ("implementer", ["--command", f"cp {HOLD_A} /tmp/peek.java"], ["denied_holdout"]),
    ("test-author", ["--path", HOLD_A], []),
    ("test-author", ["--command", f"grep -n Tag {HOLD_B}"], []),
    ("implementer", ["--path", "qa-holdout/NOTES.md"], []),
    ("implementer", ["--path", VISIBLE], []),
    ("implementer", ["--write", "--path", VISIBLE], ["denied_acceptance_lock"]),
], ids=["none-abs-read", "implementer-read", "reviewer-read", "spec-author-read",
        "implementer-write", "dot-slash-cat", "abs-sed", "stdin-redirect", "cp-out",
        "test-author-read", "test-author-grep", "unlocked-sibling", "visible-read",
        "visible-write"])
def test_ac9_policy_check(cat_locked: Path, capsys: pytest.CaptureFixture[str],
                          role: str | None, argv: list[str], denied: list[str]) -> None:
    """AC-9: holdout paths are denied with rule holdout for every role but test-author."""
    argv = [a.replace("<abs-a>", str(cat_locked / HOLD_A)).replace(
        "<abs-b>", str(cat_locked / HOLD_B)) for a in argv]
    capsys.readouterr()
    code = run(["policy", "check", *(["--role", role] if role else []), *argv, "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert [f["code"] for f in payload["findings"] if f["level"] == "error"] == denied
    assert code == (EXIT_FAIL if denied else EXIT_PASS)


def test_ac9_hooks(cat_locked: Path, monkeypatch: pytest.MonkeyPatch,
                   capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    """AC-9: Claude Code and Cursor hooks hide holdout paths; test-author (env or role file)
    may read them."""
    audit = tmp_path / "audit.jsonl"
    claude = ["policy", "hook", "--host", "claude-code", "--audit", str(audit)]
    _stdin(monkeypatch, {"tool_name": "Read", "tool_input": {"file_path": str(cat_locked / HOLD_A)},
                         "cwd": str(cat_locked)})
    assert run(claude) == 2
    assert json.loads(audit.read_text().splitlines()[-1])["rule"] == "holdout"

    monkeypatch.setenv("QR_ROLE", "implementer")
    for payload in ({"file_path": str(cat_locked / HOLD_B), "content": "",
                     "workspace_roots": [str(cat_locked)]},
                    {"command": f"grep -rn assert {HOLD_A}", "cwd": str(cat_locked)}):
        _stdin(monkeypatch, payload)
        capsys.readouterr()
        assert run(["policy", "hook", "--host", "cursor"]) == 0
        assert json.loads(capsys.readouterr().out)["permission"] == "deny"

    monkeypatch.setenv("QR_ROLE", "test-author")
    _stdin(monkeypatch, {"file_path": str(cat_locked / HOLD_B), "content": "",
                         "workspace_roots": [str(cat_locked)]})
    capsys.readouterr()
    assert run(["policy", "hook", "--host", "cursor"]) == 0
    assert json.loads(capsys.readouterr().out)["permission"] == "allow"

    monkeypatch.delenv("QR_ROLE")
    (cat_locked / ".quality-router/role").write_text("test-author\n")
    _stdin(monkeypatch, {"tool_name": "Bash", "tool_input": {"command": f"cat {HOLD_A}"},
                         "cwd": str(cat_locked)})
    assert run(claude) == 0


def test_ac9_hidden_when_files_absent(cat_locked: Path, monkeypatch: pytest.MonkeyPatch,
                                      tmp_path: Path) -> None:
    """AC-9: with the holdout files absent, reading or creating them is still denied."""
    (cat_locked / HOLD_A).unlink()
    (cat_locked / HOLD_B).unlink()
    monkeypatch.setenv("QR_ROLE", "implementer")
    audit = tmp_path / "audit.jsonl"
    for tool in ("Write", "Read"):
        _stdin(monkeypatch, {"tool_name": tool, "tool_input": {"file_path": HOLD_B},
                             "cwd": str(cat_locked)})
        assert run(["policy", "hook", "--host", "claude-code", "--audit", str(audit)]) == 2
        assert json.loads(audit.read_text().splitlines()[-1])["rule"] == "holdout"


def test_ac9_lock_without_holdout_hides_nothing(cat: Path,
                                                capsys: pytest.CaptureFixture[str]) -> None:
    """AC-9: the rule applies only when the lock has holdout entries."""
    assert _lock() == EXIT_PASS
    capsys.readouterr()
    assert run(["policy", "check", "--role", "implementer", "--path", HOLD_A]) == EXIT_PASS


# --------------------------------------------------------------------------- #
# AC-10
# --------------------------------------------------------------------------- #

def test_ac10_two_files_two_reports(cat_locked: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """AC-10: holdout tests split across reports pass; summary keys and values are exact and
    visible testcases are not counted."""
    _junit(cat_locked, "build/test-results/test/TEST-a.xml", ALL_PASS[:2], wrap=True)
    _junit(cat_locked, "build/test-results/test/TEST-b.xml",
           [ALL_PASS[2], (CLASS_VISIBLE, "ac_1", "pass"), (CLASS_VISIBLE, "ac_2", "pass")])
    code, payload = _gate(capsys)
    assert code == EXIT_PASS and payload["findings"] == [] and payload["gate"] == "holdout"
    assert payload["summary"] == {"holdout_files": 2, "holdout_tests": 3, "holdout_failed": 0,
                                  "holdout_skipped": 0, "criteria": ["AC-1", "AC-2", "AC-3"],
                                  "reports": 2}


def test_ac10_text_verdict(cat_locked: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """AC-10: the text result names gate=holdout and the summary."""
    _report(cat_locked, ALL_PASS)
    capsys.readouterr()
    assert run(["gate", "holdout", "--reports", REPORTS, "--strict"]) == EXIT_PASS
    lines = capsys.readouterr().out.splitlines()
    assert 'criteria=["AC-1", "AC-2", "AC-3"]' in lines and "holdout_files=2" in lines
    assert lines[-1].startswith("gate=holdout result=pass")


@pytest.mark.parametrize("classname,matched", [
    ("CatalogHoldoutTest", True),
    ("com.acme.catalog.CatalogHoldoutTest$Rounding", True),
    ("CatalogHoldoutTest$Rounding$HalfUp", True),
    ("other.pkg.CatalogHoldoutTest$1", True),
    ("com.acme.catalog.CatalogHoldoutTestHelper", False),
    ("com.acme.catalog.CatalogHoldoutTestHelper$Inner", False),
    ("com.acme.catalog.XCatalogHoldoutTest", False),
    ("com.acme.catalog.CatalogHoldoutTest.Rounding", False),
    ("CatalogHoldoutTests", False),
])
def test_ac10_classname_rule(cat_locked: Path, capsys: pytest.CaptureFixture[str],
                             classname: str, matched: bool) -> None:
    """AC-10: a file's tests are classnames equal to the stem, ending with .stem, or
    continuing with $ after either; similar names are not its tests."""
    _report(cat_locked, [*ALL_PASS, (classname, "probe", "fail")])
    code, payload = _gate(capsys)
    if matched:
        assert (code, _codes(payload)) == (EXIT_FAIL, ["holdout_failed"])
    else:
        assert (code, _codes(payload)) == (EXIT_PASS, [])
        assert payload["summary"]["holdout_tests"] == 3


def test_ac10_only_similar_classes_is_not_run(cat_locked: Path,
                                              capsys: pytest.CaptureFixture[str]) -> None:
    """AC-10: no testcase for a file (only similarly named classes) is holdout_not_run."""
    _report(cat_locked, [("com.acme.catalog.CatalogHoldoutTestHelper", "roundsHalfUp", "pass"),
                         (CLASS_VISIBLE, "ac_1", "pass"), ALL_PASS[2]])
    code, payload = _gate(capsys)
    assert (code, _codes(payload)) == (EXIT_FAIL, ["holdout_not_run"])


def test_ac10_mixed_pass_and_skip_passes(cat_locked: Path,
                                         capsys: pytest.CaptureFixture[str]) -> None:
    """AC-10: some skipped but not all is not holdout_not_run; skips are counted."""
    _report(cat_locked, [(CLASS_A, "roundsHalfUp", "pass"), (CLASS_A, "lowercasesTags", "skip"),
                         ALL_PASS[2]])
    code, payload = _gate(capsys)
    assert (code, _codes(payload)) == (EXIT_PASS, [])
    assert set(payload["summary"]) == SUMMARY_KEYS
    assert payload["summary"]["holdout_skipped"] == 1
    assert payload["summary"]["holdout_failed"] == 0


def test_ac10_one_file_all_skipped(cat_locked: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """AC-10: every testcase of one holdout file skipped is holdout_not_run."""
    _report(cat_locked, [(CLASS_A, "roundsHalfUp", "skip"), (CLASS_A, "lowercasesTags", "skip"),
                         ALL_PASS[2]])
    code, payload = _gate(capsys)
    assert (code, _codes(payload)) == (EXIT_FAIL, ["holdout_not_run"])


def test_ac10_failed_and_errored_named_and_counted(cat_locked: Path,
                                                   capsys: pytest.CaptureFixture[str]) -> None:
    """AC-10: failures and errors are holdout_failed, naming the methods; summary counts them."""
    _report(cat_locked, [(CLASS_A + "$Rounding", "roundsHalfUp", "fail"),
                         (CLASS_A, "lowercasesTags", "pass"),
                         (CLASS_B, "defaultsCurrency", "error")])
    code, payload = _gate(capsys)
    assert (code, _codes(payload)) == (EXIT_FAIL, ["holdout_failed"])
    named = " ".join(f"{f['path']} {f['message']}" for f in payload["findings"]
                     if f["code"] == "holdout_failed")
    assert "roundsHalfUp" in named and "defaultsCurrency" in named
    assert set(payload["summary"]) == SUMMARY_KEYS
    assert payload["summary"]["holdout_failed"] == 2


def test_ac10_visible_failure_is_not_holdout(cat_locked: Path,
                                             capsys: pytest.CaptureFixture[str]) -> None:
    """AC-10: a failing non-holdout testcase does not fail the holdout gate."""
    _report(cat_locked, [*ALL_PASS, (CLASS_VISIBLE, "ac_2", "fail")])
    code, payload = _gate(capsys)
    assert (code, _codes(payload)) == (EXIT_PASS, [])


@pytest.mark.parametrize("state", ["no-lock", "lock-without-holdout"])
def test_ac10_no_holdout_and_strict(cat: Path, capsys: pytest.CaptureFixture[str],
                                    state: str) -> None:
    """AC-10: no lock or no holdout key warns no_holdout; --strict makes it exit 1."""
    if state == "lock-without-holdout":
        assert _lock() == EXIT_PASS
    _report(cat, ALL_PASS)
    code, payload = _gate(capsys)
    assert code == EXIT_PASS and _codes(payload, "warning") == ["no_holdout"]
    assert _codes(payload) == []
    code, payload = _gate(capsys, "--strict")
    assert code == EXIT_FAIL and _codes(payload, "warning") == ["no_holdout"]


def test_ac10_strict_all_passing(cat_locked: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """AC-10: --strict passes when every holdout test ran and passed."""
    _report(cat_locked, ALL_PASS)
    code, payload = _gate(capsys, "--strict")
    assert code == EXIT_PASS and payload["findings"] == []


def test_ac10_reports_match_nothing(cat_locked: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """AC-10: a reports pattern that matches nothing is a usage error on stderr."""
    _report(cat_locked, ALL_PASS)
    capsys.readouterr()
    assert run(["gate", "holdout", "--reports", "build/test-results/**/NOPE-*.xml"]) \
        == EXIT_USAGE
    assert "Error: JUnit report not found" in capsys.readouterr().err


def test_ac10_one_of_two_missing(cat_locked: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """AC-10: one absent holdout file is holdout_missing."""
    _report(cat_locked, ALL_PASS)
    (cat_locked / HOLD_B).unlink()
    code, payload = _gate(capsys)
    assert (code, _codes(payload)) == (EXIT_FAIL, ["holdout_missing"])


def test_ac10_one_byte_changed(cat_locked: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """AC-10: a single changed byte is holdout_modified."""
    _report(cat_locked, ALL_PASS)
    (cat_locked / HOLD_A).write_bytes((cat_locked / HOLD_A).read_bytes() + b"\n")
    code, payload = _gate(capsys)
    assert (code, _codes(payload)) == (EXIT_FAIL, ["holdout_modified"])


def test_ac10_tracked_now(cat_locked: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """AC-10: a holdout file tracked by git is holdout_exposed."""
    _report(cat_locked, ALL_PASS)
    _force_commit(cat_locked, HOLD_B, "edge holdout leaked")
    code, payload = _gate(capsys)
    assert (code, _codes(payload)) == (EXIT_FAIL, ["holdout_exposed"])


def test_ac10_touched_in_range_then_untracked(cat_locked: Path,
                                              capsys: pytest.CaptureFixture[str]) -> None:
    """AC-10: a commit in REF..HEAD touching a holdout path is holdout_exposed even after the
    file is untracked again; an empty range is not."""
    _report(cat_locked, ALL_PASS)
    base = _git(cat_locked, "rev-parse", "HEAD")
    _force_commit(cat_locked, HOLD_A, "add holdout")
    _git(cat_locked, "rm", "-q", "--cached", HOLD_A)
    _git(cat_locked, "commit", "-qm", "drop holdout from index")
    assert (cat_locked / HOLD_A).read_text() == HOLD_A_SRC
    code, payload = _gate(capsys, "--base", base)
    assert (code, _codes(payload)) == (EXIT_FAIL, ["holdout_exposed"])
    code, payload = _gate(capsys, "--base", "HEAD")
    assert (code, _codes(payload)) == (EXIT_PASS, [])


def test_ac10_non_git_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                           capsys: pytest.CaptureFixture[str]) -> None:
    """AC-10: in a root that is not a git work tree the holdout files are untracked."""
    plain = tmp_path / "unversioned"
    _seed(plain)
    _holdouts(plain)
    monkeypatch.chdir(plain)
    assert _lock("--holdout", HOLD_GLOB) == EXIT_PASS
    _report(plain, ALL_PASS)
    code, payload = _gate(capsys)
    assert (code, payload["findings"]) == (EXIT_PASS, [])


def test_ac10_root_flag_with_absolute_reports(cat_locked: Path, tmp_path: Path,
                                              monkeypatch: pytest.MonkeyPatch,
                                              capsys: pytest.CaptureFixture[str]) -> None:
    """AC-10: --root selects the lock and holdout files when run from another directory."""
    _report(cat_locked, ALL_PASS)
    elsewhere = tmp_path / "ci-work"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    code, payload = _gate(capsys, "--root", str(cat_locked),
                          reports=str(cat_locked / "build/test-results/**/*.xml"))
    assert (code, payload["findings"]) == (EXIT_PASS, [])
    assert payload["summary"]["holdout_files"] == 2


def test_ac10_gate_holdout_module(cat_locked: Path) -> None:
    """AC-10: gate_holdout returns a GateResult named holdout; strict turns no_holdout red."""
    from quality_router.harness.acceptance import gate_holdout

    report = _report(cat_locked, ALL_PASS)
    result = gate_holdout(cat_locked, [report], base=None, strict=True)
    assert result.gate == "holdout" and result.passed
    assert result.summary["criteria"] == ["AC-1", "AC-2", "AC-3"]
    (cat_locked / LOCK_FILE).unlink()
    lenient = gate_holdout(cat_locked, [report])
    assert lenient.passed and [f.code for f in lenient.findings] == ["no_holdout"]
    assert not gate_holdout(cat_locked, [report], strict=True).passed


# --------------------------------------------------------------------------- #
# AC-11
# --------------------------------------------------------------------------- #

def test_ac11_acceptance_ignores_holdout_changes(cat_locked: Path,
                                                 capsys: pytest.CaptureFixture[str]) -> None:
    """AC-11: gate acceptance ignores holdout entries: modified, tracked or absent."""
    base = _git(cat_locked, "rev-parse", "HEAD~1")
    _put(cat_locked, HOLD_A, HOLD_A_SRC + "// edited\n")
    assert run(["gate", "acceptance"]) == EXIT_PASS
    _force_commit(cat_locked, HOLD_A, "holdout committed")
    assert run(["gate", "acceptance", "--base", base]) == EXIT_PASS
    (cat_locked / HOLD_B).unlink()
    capsys.readouterr()
    assert run(["gate", "acceptance", "--json"]) == EXIT_PASS
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is True and payload["errors"] == 0


def test_ac11_module_counts_visible_tests_only(cat_locked: Path) -> None:
    """AC-11: gate_acceptance passes with holdout files absent and counts only --tests."""
    from quality_router.harness.acceptance import gate_acceptance

    (cat_locked / HOLD_A).unlink()
    (cat_locked / HOLD_B).unlink()
    result = gate_acceptance(cat_locked)
    assert result.passed and result.errors == 0
    assert result.summary["locked_tests"] == 1


def test_ac11_visible_tamper_still_fails(cat_locked: Path,
                                         capsys: pytest.CaptureFixture[str]) -> None:
    """AC-11: with a holdout lock, a changed visible test still fails gate acceptance."""
    _put(cat_locked, VISIBLE, VISIBLE_SRC.replace("ac_3", "ac_3_weakened"))
    capsys.readouterr()
    assert run(["gate", "acceptance"]) == EXIT_FAIL
    assert "locked_test_modified" in capsys.readouterr().out


def test_ac11_lock_without_holdout_protects(cat: Path, monkeypatch: pytest.MonkeyPatch,
                                            tmp_path: Path) -> None:
    """AC-11: a lock without holdout loads and its files stay write-protected."""
    from quality_router.harness.acceptance import load_lock

    assert _lock() == EXIT_PASS
    _commit_all(cat, "lock")
    assert "holdout" not in load_lock(cat / LOCK_FILE)
    audit = tmp_path / "audit.jsonl"
    hook = ["policy", "hook", "--host", "claude-code", "--audit", str(audit)]
    _stdin(monkeypatch, {"tool_name": "Edit", "tool_input": {"file_path": VISIBLE},
                         "cwd": str(cat)})
    assert run(hook) == 2
    assert json.loads(audit.read_text().splitlines()[-1])["rule"] == "acceptance_lock"
    _stdin(monkeypatch, {"tool_name": "Read", "tool_input": {"file_path": VISIBLE},
                         "cwd": str(cat)})
    assert run(hook) == 0


# --------------------------------------------------------------------------- #
# AC-12
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("argv,needles", [
    (["gate", "holdout", "--help"], ["--reports", "--base", "--strict", "--json", "--root"]),
    (["policy", "check", "--help"], ["--role"]),
    (["policy", "hook", "--help"], ["--role"]),
    (["spec", "lock", "--help"], ["--holdout", "--tests"]),
    (["gate", "--help"], ["qr gate holdout", "acceptance"]),
])
def test_ac12_help(capsys: pytest.CaptureFixture[str], argv: list[str],
                   needles: list[str]) -> None:
    """AC-12: help output shows the new options and the gate holdout example."""
    capsys.readouterr()
    with pytest.raises(SystemExit) as exc:
        run(argv)
    assert exc.value.code == 0
    out = capsys.readouterr().out
    for needle in needles:
        assert needle in out
