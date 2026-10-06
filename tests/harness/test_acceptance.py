"""Acceptance lock, `qr gate acceptance`, lock-aware policy, and JUnit repair feedback."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.helpers import git
from quality_router.harness import acceptance
from quality_router.harness.acceptance import (
    LOCK_PATH,
    AcceptanceError,
    build_lock,
    find_lock,
    gate_acceptance,
    load_lock,
    locked_files,
    write_lock,
)
from quality_router.harness.junit_feedback import (
    _csv_row,
    _frames,
    enrich,
    parse_reports,
    render_json,
    render_text,
)
from quality_router.harness.policy import HookEvent, Policy, check_locked, decide
from quality_router.harness.specdoc import parse_spec

SPEC = """\
Contract: `spec.md`
### AC-1 Title is trimmed
| title | expected title |
| --- | --- |
| `  Intro ` | Intro |
### AC-2 Licence
| manifest | expected licenseId |
| --- | --- |
| `lang=en` | UNLICENSED |
| (null) | UNLICENSED |
"""
ACCEPTANCE_TEST = """\
package demo;
class ItemAcceptanceTest {
    @ParameterizedTest(name = "AC-1 [{index}] {arguments}")
    @Tag("AC-1")
    @CsvSource(delimiter = '|', nullValues = "(null)", textBlock = \"\"\"
            '  Intro ' | Intro
            \"\"\"
    )
    void ac_1(String title, String expectedTitle) {
        assertEquals(expectedTitle, svc.title(title));
    }

    @ParameterizedTest
    @Tag("AC-2")
    @CsvSource(delimiter = '|', nullValues = "(null)", textBlock = \"\"\"
            # comment rows are skipped by JUnit
            lang=en | UNLICENSED
            (null) | UNLICENSED
            \"\"\"
    )
    void ac_2(String manifest, String expectedLicenseId) {
        assertEquals(expectedLicenseId, svc.license(manifest));
    }
}
"""
TEST_REL = "src/test/java/demo/ItemAcceptanceTest.java"


def commit(root: Path, message: str) -> str:
    git(root, "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@x", "commit", "-qm", message)
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def locked(repo: Path) -> tuple[Path, str]:
    """Repo with spec + acceptance test locked in its own commit, on top of a base commit."""
    (repo / "README.md").write_text("x\n")
    base = commit(repo, "base")
    (repo / "specs").mkdir()
    (repo / "specs/item.md").write_text(SPEC)
    test = repo / TEST_REL
    test.parent.mkdir(parents=True)
    test.write_text(ACCEPTANCE_TEST)
    lock = build_lock(repo, [repo / "specs/item.md"], [test], None, approved_by="qa")
    write_lock(repo, lock)
    commit(repo, "spec: lock")
    return repo, base


def codes(result) -> list[str]:
    return [f.code for f in result.findings]


def implement(repo: Path, text: str = "class Svc {}\n") -> str:
    src = repo / "src/main/java/demo/Svc.java"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text(text)
    return commit(repo, "impl")


class TestLock:
    def test_lock_document(self, locked) -> None:
        repo, _ = locked
        lock = load_lock(repo / LOCK_PATH)
        assert lock["owned"] == ["AC-1", "AC-2"] and lock["approved_by"] == "qa"
        assert lock["tests"][TEST_REL]["criteria"] == ["AC-1", "AC-2"]
        assert lock["specs"]["specs/item.md"]["criteria"] == ["AC-1", "AC-2"]
        assert find_lock(repo / "src/test") == repo / LOCK_PATH
        assert (repo / TEST_REL).resolve() in locked_files(repo / LOCK_PATH)

    def test_build_errors(self, repo: Path) -> None:
        spec = repo / "s.md"
        spec.write_text(SPEC)
        test = repo / "T.java"
        test.write_text('@Tag("AC-1") void t() {}')
        with pytest.raises(AcceptanceError, match="not found"):
            build_lock(repo, [spec], [repo / "missing.java"], None)
        with pytest.raises(AcceptanceError, match="no test files"):
            build_lock(repo, [spec], [], None)
        with pytest.raises(AcceptanceError, match="not in spec"):
            build_lock(repo, [spec], [test], ["AC-9"])
        with pytest.raises(AcceptanceError, match=r"no locked test: \['AC-2'\]"):
            build_lock(repo, [spec], [test], None)
        assert build_lock(repo, [spec], [test], ["AC-1"])["owned"] == ["AC-1"]

    @pytest.mark.parametrize("text,match", [
        ("{", "invalid JSON"),
        ('{"version": 2}', "version-1"),
        ('{"version": 1, "specs": {}, "tests": {"a": {}}}', "tests"),
    ])
    def test_bad_lock(self, tmp_path: Path, text: str, match: str) -> None:
        path = tmp_path / "lock.json"
        path.write_text(text)
        with pytest.raises(AcceptanceError, match=match):
            load_lock(path)


class TestGate:
    def test_no_lock_warns(self, tmp_path: Path) -> None:
        result = gate_acceptance(tmp_path)
        assert codes(result) == ["no_acceptance_lock"] and result.passed
        assert not gate_acceptance(tmp_path, strict=True).passed

    def test_approve_then_implement_passes(self, locked) -> None:
        repo, base = locked
        implement(repo)
        result = gate_acceptance(repo, base)
        assert result.passed, codes(result)
        assert codes(result) == ["acceptance_relocked"]
        assert gate_acceptance(repo).findings == []
        assert result.summary["locked_tests"] == 1 and result.summary["approved_by"] == "qa"

    def test_tampered_and_removed_tests_fail(self, locked) -> None:
        repo, _ = locked
        test = repo / TEST_REL
        test.write_text(ACCEPTANCE_TEST.replace("            (null) | UNLICENSED\n", ""))
        assert codes(gate_acceptance(repo)) == ["locked_test_modified"]
        test.unlink()
        assert codes(gate_acceptance(repo)) == ["locked_test_missing"]

    def test_spec_changed_or_not_checked_out(self, locked) -> None:
        repo, _ = locked
        spec = repo / "specs/item.md"
        spec.write_text(SPEC + "| `x` | y |\n")
        assert codes(gate_acceptance(repo)) == ["spec_changed_since_lock"]
        spec.unlink()
        assert codes(gate_acceptance(repo)) == ["spec_not_checked_out"]

    def test_relock_after_implementation_fails(self, locked) -> None:
        repo, base = locked
        implement(repo)
        test = repo / TEST_REL
        test.write_text(ACCEPTANCE_TEST.replace("            (null) | UNLICENSED\n", ""))
        write_lock(repo, build_lock(repo, [repo / "specs/item.md"], [test], None))
        commit(repo, "agent relock")
        assert gate_acceptance(repo).passed
        result = gate_acceptance(repo, base)
        assert "implementation_before_lock" in codes(result) and not result.passed

    def test_lock_commit_with_implementation_fails(self, repo: Path) -> None:
        (repo / "specs").mkdir()
        (repo / "specs/item.md").write_text(SPEC)
        (repo / "src/test/java/demo").mkdir(parents=True)
        (repo / TEST_REL).write_text(ACCEPTANCE_TEST)
        (repo / "src/main/java").mkdir(parents=True)
        (repo / "src/main/java/Svc.java").write_text("class Svc {}\n")
        write_lock(repo, build_lock(repo, [repo / "specs/item.md"], [repo / TEST_REL], None))
        commit(repo, "lock and code together")
        assert "lock_commit_has_implementation" in codes(gate_acceptance(repo))

    def test_history_unavailable_and_bad_base(self, locked, tmp_path: Path) -> None:
        repo, _ = locked
        with pytest.raises(AcceptanceError, match="cannot list"):
            gate_acceptance(repo, "no-such-ref")
        copy = tmp_path / "copy"
        (copy / ".quality-router").mkdir(parents=True)
        (copy / LOCK_PATH).write_text((repo / LOCK_PATH).read_text())
        (copy / "specs").mkdir()
        (copy / "specs/item.md").write_text(SPEC)
        (copy / TEST_REL).parent.mkdir(parents=True)
        (copy / TEST_REL).write_text(ACCEPTANCE_TEST)
        assert codes(gate_acceptance(copy)) == ["lock_history_unavailable"]
        assert acceptance._git(copy, "rev-parse", "HEAD") is None


class TestPolicyLock:
    def test_writes_denied_reads_allowed(self, locked) -> None:
        repo, _ = locked
        files = locked_files(repo / LOCK_PATH)
        policy = Policy()
        cwd = str(repo)
        deny = [
            HookEvent("path", TEST_REL, cwd, "write"),
            HookEvent("path", str(repo / LOCK_PATH), "", "write"),
            HookEvent("command", f"sed -i '/null/d' {TEST_REL}", cwd),
            HookEvent("command", f"echo x >{TEST_REL}", cwd),
            HookEvent("command", "git checkout HEAD~1 -- specs/item.md", cwd),
            HookEvent("command", "qr spec lock --spec specs/item.md --tests x", cwd),
        ]
        for event in deny:
            decision = decide(event, policy, repo, files)
            assert not decision.allow and decision.rule == "acceptance_lock", event
        allow = [
            HookEvent("path", TEST_REL, cwd, "read"),
            HookEvent("path", "src/main/java/demo/Svc.java", cwd, "write"),
            HookEvent("command", f"cat {TEST_REL}", cwd),
            HookEvent("command", "rm -f target/x.class", cwd),
            HookEvent("command", "echo 'unbalanced > x", cwd),
        ]
        for event in allow:
            assert decide(event, policy, repo, files).allow, event
        assert check_locked(HookEvent("path", TEST_REL, "", "write"), files, repo).rule \
            == "acceptance_lock"


REPORT = """\
<testsuites>
<testsuite name="s">
  <testcase name="ac_2(String, String)[2]" classname="demo.ItemAcceptanceTest">
    <error message="Cannot invoke &quot;String.split&quot; because m is null"
           type="java.lang.NullPointerException">java.lang.NullPointerException: boom
    at demo.LicenseParser.parse(LicenseParser.java:12)
    at java.base/java.lang.String.split(String.java:1)
    at demo.ItemAcceptanceTest.ac_2(ItemAcceptanceTest.java:22)
    at org.junit.platform.Runner.run(Runner.java:1)
Caused by: java.lang.IllegalStateException
    at demo.Deep.call(Deep.java:3)</error>
  </testcase>
  <testcase name="ac_1(String, String)[1]" classname="demo.ItemAcceptanceTest">
    <failure message="expected: &lt;Intro&gt; but was: &lt;  Intro &gt;"
             type="org.opentest4j.AssertionFailedError">trace</failure>
  </testcase>
  <testcase name="legacy" classname="demo.Other$Inner">
    <failure message="expected: 3 but was: 4" type="AssertionError"/>
  </testcase>
  <testcase name="passes" classname="demo.ItemAcceptanceTest"/>
  <testcase name="silent" classname="demo.Gone"><failure/></testcase>
</testsuite>
</testsuites>
"""


class TestJunitFeedback:
    def test_parse_enrich_render(self, locked, tmp_path: Path) -> None:
        repo, _ = locked
        report = tmp_path / "TEST-x.xml"
        report.write_text(REPORT)
        (repo / "src/test/java/demo/Other.java").write_text("class Other {\n  @Test\n"
                                                            "  void legacy() {}\n}\n")
        total, failures = parse_reports([report], max_frames=3)
        assert total == 5 and len(failures) == 4
        npe, title, legacy, silent = failures
        assert npe.invocation == 2 and npe.kind == "error" and npe.expected is None
        assert npe.frames == ["at demo.LicenseParser.parse(LicenseParser.java:12)",
                              "at demo.ItemAcceptanceTest.ac_2(ItemAcceptanceTest.java:22)",
                              "Caused by: java.lang.IllegalStateException"]
        assert (title.expected, title.actual) == ("Intro", "Intro")
        assert (legacy.expected, legacy.actual) == ("3", "4")
        assert silent.message == ""
        enrich(failures, [repo / "src/test/java", tmp_path / "nowhere"],
               [parse_spec(repo / "specs/item.md")])
        assert npe.criteria == ["AC-2"] and npe.title == "Licence"
        assert npe.source.endswith(TEST_REL) and npe.line == 13
        assert npe.test_row == "(null) | UNLICENSED"
        assert npe.example is not None and npe.example.cells == ["(null)", "UNLICENSED"]
        assert npe.example.line == 10
        assert legacy.source.endswith("Other.java") and legacy.criteria == []
        assert silent.source == ""
        text = render_text(total, failures)
        assert "FAIL AC-2 Licence [invocation 2]" in text
        assert "example  " in text and "| (null) | UNLICENSED |" in text
        assert "assert   expected <3> but was <4>" in text
        assert "error    java.lang.NullPointerException: Cannot invoke" in text
        assert "source not found (pass --sources)" in text
        assert text.rstrip().endswith("junit_tests=5 failures=4 result=fail")
        payload = json.loads(render_json(total, failures))
        assert payload["failed"] == 4 and payload["failures"][0]["example"]["line"] == 10
        assert render_text(1, []).strip() == "junit_tests=1 failures=0 result=pass"

    def test_row_fallback_without_spec(self, locked, tmp_path: Path) -> None:
        repo, _ = locked
        report = tmp_path / "r.xml"
        report.write_text(REPORT)
        _, failures = parse_reports([report])
        enrich(failures, [repo / "src/test/java"], [])
        assert failures[0].example is None and "row      (null) | UNLICENSED" in render_text(
            5, failures[:1])
        assert failures[0].criteria == ["AC-2"] and failures[0].title == ""

    def test_helpers(self) -> None:
        assert _frames("at java.lang.X(X.java:1)\n", 5) == []
        lines = ['textBlock = """', "a | b", '"""']
        assert _csv_row(lines, 1, 3, 1) == "a | b" and _csv_row(lines, 1, 3, 2) == ""
