"""qr eval: leak-free task workspaces and per host@version/model regression reports."""

from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

import pytest

from harness.helpers import git
from quality_router.harness.evalkit import (
    _safe_members,
    eval_report,
    load_runs,
    prepare_task,
    summarize,
    wilson,
)


@pytest.fixture
def service(repo: Path) -> tuple[Path, str]:
    (repo / "src/main").mkdir(parents=True)
    (repo / "src/test").mkdir(parents=True)
    (repo / "src/main/App.java").write_text("class App {}\n")
    (repo / "src/test/HiddenTest.java").write_text("class HiddenTest {}\n")
    (repo / "src/test/fixtures").mkdir()
    (repo / "src/test/fixtures/a.json").write_text("{}")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    base = git(repo, "rev-parse", "HEAD")
    (repo / "src/main/Future.java").write_text("class Future {}\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "the fix (must not leak)")
    return repo, base


class TestPrepare:
    def test_snapshot_has_no_history_and_hides_tests(self, service, tmp_path: Path) -> None:
        repo, base = service
        out = tmp_path / "task"
        manifest = prepare_task(repo, base, ["src/test/HiddenTest.java", "src/test/fixtures"],
                                out, "ING-1", "fix it")
        ws = out / "workspace"
        assert (ws / "src/main/App.java").is_file()
        assert not (ws / "src/main/Future.java").exists()
        assert not (ws / "src/test/HiddenTest.java").exists()
        assert (out / "hidden/src/test/HiddenTest.java").is_file()
        assert git(ws, "rev-list", "--count", "HEAD") == "1"
        assert git(ws, "remote") == ""
        assert manifest["base_commit"] == base
        assert set(manifest["hidden"]) == {"src/test/HiddenTest.java", "src/test/fixtures"}
        assert json.loads((out / "task.json").read_text())["prompt"] == "fix it"

    def test_refuses_non_empty_out_and_missing_hidden(self, service, tmp_path: Path) -> None:
        repo, base = service
        busy = tmp_path / "busy"
        busy.mkdir()
        (busy / "x").write_text("")
        with pytest.raises(FileExistsError):
            prepare_task(repo, base, [], busy, "t", None)
        with pytest.raises(FileNotFoundError):
            prepare_task(repo, base, ["nope.java"], tmp_path / "o", "t", None)
        with pytest.raises(RuntimeError):
            prepare_task(repo, "no-such-ref", [], tmp_path / "o2", "t", None)

    def test_safe_members_drop_escapes_and_links(self) -> None:
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as archive:
            for name in ("ok.txt", "../escape.txt", "/abs.txt"):
                info = tarfile.TarInfo(name)
                archive.addfile(info, io.BytesIO(b""))
            link = tarfile.TarInfo("link")
            link.type = tarfile.SYMTYPE
            link.linkname = "/etc/passwd"
            archive.addfile(link)
        buf.seek(0)
        with tarfile.open(fileobj=buf) as archive:
            assert [m.name for m in _safe_members(archive)] == ["ok.txt"]


def run(task: str, resolved: bool, host: str = "claude-code", version: str = "2.1",
        model: str = "m", tokens: int | None = 100) -> dict:
    record = {"task": task, "host": host, "host_version": version, "model": model,
              "resolved": resolved, "tool_calls": 3}
    if tokens is not None:
        record["tokens"] = tokens
    return record


class TestReport:
    def test_wilson(self) -> None:
        assert wilson(0, 0) == (0.0, 0.0)
        low, high = wilson(8, 10)
        assert 0.44 < low < 0.5 and 0.94 < high < 0.95

    def test_summary_flips_and_tokens(self) -> None:
        runs = [run("a", True), run("a", False), run("b", True), run("c", False, tokens=None)]
        (stats,) = summarize(runs)
        assert stats.key == "claude-code@2.1/m"
        assert (stats.runs, stats.tasks, stats.resolved) == (4, 3, 2)
        assert stats.flip_rate == 1.0
        assert stats.tokens_per_resolved == 150.0
        assert summarize([run("a", False, tokens=None)])[0].tokens_median is None

    def test_regression_rules(self) -> None:
        base = [run(f"t{i}", True) for i in range(30)]
        worse = [run(f"t{i}", i < 10, version="2.2", tokens=400) for i in range(30)]
        noisy = [run(f"t{i}", i != 0, host="cursor", version="1", tokens=None)
                 for i in range(30)]
        noisy += [run("t1", False, host="cursor", version="1")]
        result = eval_report(base + worse + noisy, "claude-code@2.1/m", 0.25, 0.05)
        found = {(f.code, f.path) for f in result.findings}
        assert ("resolve_rate_regression", "claude-code@2.2/m") in found
        assert ("token_regression", "claude-code@2.2/m") in found
        assert ("resolve_rate_drop", "cursor@1/m") in found
        assert not result.passed
        assert result.summary["claude-code@2.1/m"]["resolve_rate"] == 1.0

    def test_small_suite_and_missing_baseline(self) -> None:
        runs = [run("a", True, version="")]
        report = eval_report(runs, None, 0.25, 0.05)
        assert [f.code for f in report.findings] == ["small_suite"]
        assert "claude-code@?/m" in report.summary
        missing = eval_report(runs, "x@1/y", 0.25, 0.05)
        assert "baseline_missing" in [f.code for f in missing.findings]

    def test_load_runs(self, tmp_path: Path) -> None:
        path = tmp_path / "runs.jsonl"
        path.write_text(json.dumps(run("a", True)) + "\n\n")
        assert len(load_runs(path)) == 1
        path.write_text('{"task": "a"}\n')
        with pytest.raises(ValueError, match="missing"):
            load_runs(path)
