"""Phase 6 section B: `qr init --graph gortex` evidence-aligned `.gortex.yaml` (AC-15 .. AC-23).

Spec: docs/design/phase-6-api-compat-and-gortex.md. `gortex` on PATH is faked by
patching `quality_router.init.shutil.which`; no test runs gortex.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from quality_router.cli import run
from quality_router.harness.yamlsubset import loads
from quality_router.init import InitConfig, _write_gortex_config, run_init

HEADER = """\
# Written by `qr init --graph gortex`. qr never overwrites this file.
# Settings follow research/harness-kb/implementations.md (quality-router):
#   embedding off: embedding indexes are poisonable and localize Java poorly
#   facade-v1 in hide mode: about 15 inlined tools still select well
#   Java Kafka boundaries declared: Gortex does not detect them for Java
"""

BODY = """\
embedding:
  enabled: false
mcp:
  tools:
    preset: facade-v1
    mode: hide
index:
  event_bus:
    - name: kafka
      type: producer
      callee: kafkaTemplate.send
      topic_arg: "0"
    - name: kafka
      type: consumer
      decorator: KafkaListener
      topic_arg: topics
"""

AC15_TEXT = HEADER + 'workspace: "my-service"\n' + BODY

CONTENT_MODEL_BLOCK = """\
cross_workspace_deps:
  - workspace: "content-model"
    modules:
      - "edu.acme:content-model"
      - "edu.acme:content-events"
    mode: read-only
"""

LOADED_BASE = {
    "embedding": {"enabled": False},
    "mcp": {"tools": {"preset": "facade-v1", "mode": "hide"}},
    "index": {"event_bus": [
        {"name": "kafka", "type": "producer", "callee": "kafkaTemplate.send",
         "topic_arg": "0"},
        {"name": "kafka", "type": "consumer", "decorator": "KafkaListener",
         "topic_arg": "topics"},
    ]},
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def gortex_on_path(monkeypatch: pytest.MonkeyPatch, present: bool) -> None:
    def fake_which(name: str, *_args, **_kwargs) -> str | None:
        return "/usr/bin/gortex" if present and name == "gortex" else None

    monkeypatch.setattr("quality_router.init.shutil.which", fake_which)


def qr(*argv: str) -> int:
    try:
        return run(list(argv))
    except SystemExit as exc:
        if exc.code is None:
            return 0
        return exc.code if isinstance(exc.code, int) else 2


def init_in(ws: Path, monkeypatch: pytest.MonkeyPatch, *argv: str) -> int:
    monkeypatch.chdir(ws)
    return qr("init", *argv)


def block_processes(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_a, **_k):
        raise AssertionError("qr init must not start a process for gortex")

    monkeypatch.setattr(subprocess, "run", boom)
    monkeypatch.setattr(subprocess, "Popen", boom)
    monkeypatch.setattr(os, "system", boom)


@pytest.fixture
def ws(tmp_path: Path) -> Path:
    path = tmp_path / "svc"
    path.mkdir()
    return path


# --------------------------------------------------------------------------- #
# AC-15
# --------------------------------------------------------------------------- #

class TestAC15StampedSettings:
    """AC-15: with gortex on PATH and no deps, `.gortex.yaml` is exactly the spec text."""

    def test_cli_exact_text(self, ws: Path, monkeypatch, capsys) -> None:
        """AC-15: `init --graph gortex --workspace my-service` writes the spec block."""
        gortex_on_path(monkeypatch, True)
        assert init_in(ws, monkeypatch, "--graph", "gortex", "--workspace", "my-service") == 0
        assert (ws / ".gortex.yaml").read_text(encoding="utf-8") == AC15_TEXT
        assert "gortex_config=written" in capsys.readouterr().out.splitlines()

    def test_module_exact_text(self, ws: Path, monkeypatch) -> None:
        """AC-15: _write_gortex_config returns "written" and writes the spec block."""
        gortex_on_path(monkeypatch, True)
        assert _write_gortex_config(ws, "my-service", []) == "written"
        assert (ws / ".gortex.yaml").read_text(encoding="utf-8") == AC15_TEXT

    def test_run_init_returns_status(self, ws: Path, monkeypatch) -> None:
        """AC-15: run_init returns the gortex status."""
        gortex_on_path(monkeypatch, True)
        status = run_init(InitConfig(cwd=ws, graph="gortex", workspace="my-service"))
        assert status == "written"
        assert (ws / ".gortex.yaml").read_text(encoding="utf-8") == AC15_TEXT

    def test_workspace_defaults_to_directory_name(self, tmp_path: Path, monkeypatch) -> None:
        """AC-15: without --workspace the directory name is the (quoted) workspace."""
        gortex_on_path(monkeypatch, True)
        repo = tmp_path / "billing-svc"
        repo.mkdir()
        assert init_in(repo, monkeypatch, "--graph", "gortex") == 0
        assert (repo / ".gortex.yaml").read_text(encoding="utf-8") == (
            HEADER + 'workspace: "billing-svc"\n' + BODY)


# --------------------------------------------------------------------------- #
# AC-16
# --------------------------------------------------------------------------- #

DEP_ROWS = [
    (["--workspace-dep", "a", "--module", "x"], [("a", ["x"])]),
    (["--workspace-dep", "a", "--module", "x", "--workspace-dep", "b", "--module", "y"],
     [("a", ["x"]), ("b", ["y"])]),
    (["--workspace-dep", "a", "--module", "x", "--workspace-dep", "a", "--module", "y",
      "--workspace-dep", "a", "--module", "x"], [("a", ["x", "y"])]),
    (["--workspace-dep", "a", "--workspace-dep", "b"], [("a", ["."]), ("b", ["."])]),
]


class TestAC16CrossWorkspaceDeps:
    """AC-16: --workspace-dep/--module pairs merge into read-only module lists."""

    def test_block_text_after_workspace_line(self, ws: Path, monkeypatch) -> None:
        """AC-16: the documented block, right after the `workspace:` line."""
        gortex_on_path(monkeypatch, True)
        code = init_in(ws, monkeypatch, "--graph", "gortex", "--workspace", "s",
                       "--workspace-dep", "content-model", "--module", "edu.acme:content-model",
                       "--workspace-dep", "content-model", "--module",
                       "edu.acme:content-events")
        assert code == 0
        assert (ws / ".gortex.yaml").read_text(encoding="utf-8") == (
            HEADER + 'workspace: "s"\n' + CONTENT_MODEL_BLOCK + BODY)

    @pytest.mark.parametrize(("deps", "entries"), DEP_ROWS)
    def test_entry_rows(self, deps: list[str], entries: list[tuple[str, list[str]]], ws: Path,
                        monkeypatch) -> None:
        """AC-16: example table rows (merge, order, default module `.`)."""
        gortex_on_path(monkeypatch, True)
        assert init_in(ws, monkeypatch, "--graph", "gortex", "--workspace", "s", *deps) == 0
        loaded = loads((ws / ".gortex.yaml").read_text(encoding="utf-8"))
        assert loaded["cross_workspace_deps"] == [
            {"workspace": name, "modules": modules, "mode": "read-only"}
            for name, modules in entries
        ]

    def test_module_values_are_double_quoted(self, ws: Path, monkeypatch) -> None:
        """AC-16: every user value is double-quoted, including the default module."""
        gortex_on_path(monkeypatch, True)
        assert init_in(ws, monkeypatch, "--graph", "gortex", "--workspace", "s",
                       "--workspace-dep", "a") == 0
        lines = (ws / ".gortex.yaml").read_text(encoding="utf-8").splitlines()
        assert '  - workspace: "a"' in lines
        assert '      - "."' in lines
        assert "    mode: read-only" in lines

    def test_module_api_pairs(self, ws: Path, monkeypatch) -> None:
        """AC-16: _write_gortex_config accepts (workspace, module) pairs."""
        gortex_on_path(monkeypatch, True)
        assert _write_gortex_config(ws, "s", [("a", "x")]) == "written"
        loaded = loads((ws / ".gortex.yaml").read_text(encoding="utf-8"))
        assert loaded["cross_workspace_deps"] == [
            {"workspace": "a", "modules": ["x"], "mode": "read-only"}]


# --------------------------------------------------------------------------- #
# AC-17
# --------------------------------------------------------------------------- #

class TestAC17LoadsAsMapping:
    """AC-17: yamlsubset.loads reads the stamped file into the documented mapping."""

    @pytest.mark.parametrize(("deps", "expected"), [
        ([], None),
        (["--workspace-dep", "a", "--module", "x"],
         [{"workspace": "a", "modules": ["x"], "mode": "read-only"}]),
    ])
    def test_loaded_rows(self, deps: list[str], expected, ws: Path, monkeypatch) -> None:
        """AC-17: example table rows; cross_workspace_deps absent without dependencies."""
        gortex_on_path(monkeypatch, True)
        assert init_in(ws, monkeypatch, "--graph", "gortex", "--workspace", "s", *deps) == 0
        loaded = loads((ws / ".gortex.yaml").read_text(encoding="utf-8"))
        want = {"workspace": "s", **LOADED_BASE}
        if expected is None:
            assert "cross_workspace_deps" not in loaded
        else:
            want["cross_workspace_deps"] = expected
        assert loaded == want

    def test_same_input_same_bytes(self, tmp_path: Path, monkeypatch) -> None:
        """AC-17: the same input always produces the same bytes."""
        gortex_on_path(monkeypatch, True)
        outputs = []
        for name in ("one", "two"):
            repo = tmp_path / name
            repo.mkdir()
            assert init_in(repo, monkeypatch, "--graph", "gortex", "--workspace", "s",
                           "--workspace-dep", "a", "--module", "x",
                           "--workspace-dep", "b", "--module", "y") == 0
            outputs.append((repo / ".gortex.yaml").read_bytes())
        assert outputs[0] == outputs[1]


# --------------------------------------------------------------------------- #
# AC-18
# --------------------------------------------------------------------------- #

class TestAC18Disconnected:
    """AC-18: without gortex on PATH nothing is written; status is disconnected."""

    @pytest.mark.parametrize(("present", "written", "line"), [
        (False, False, "gortex_config=disconnected"),
        (True, True, "gortex_config=written"),
    ])
    def test_rows(self, present: bool, written: bool, line: str, ws: Path, monkeypatch,
                  capsys) -> None:
        """AC-18: example table rows."""
        gortex_on_path(monkeypatch, present)
        assert init_in(ws, monkeypatch, "--graph", "gortex", "--workspace", "s") == 0
        assert (ws / ".gortex.yaml").exists() is written
        assert line in capsys.readouterr().out.splitlines()

    def test_stderr_names_signed_package(self, ws: Path, monkeypatch, capsys) -> None:
        """AC-18: stderr says gortex not on PATH, names brew, never curl/| sh/irm."""
        gortex_on_path(monkeypatch, False)
        assert init_in(ws, monkeypatch, "--graph", "gortex", "--workspace", "s") == 0
        err = capsys.readouterr().err
        assert "gortex not on PATH" in err
        assert "brew install zzet/tap/gortex" in err
        for bad in ("curl", "| sh", "irm"):
            assert bad not in err

    def test_module_returns_disconnected(self, ws: Path, monkeypatch) -> None:
        """AC-18: _write_gortex_config and run_init return "disconnected"."""
        gortex_on_path(monkeypatch, False)
        assert _write_gortex_config(ws, "s", []) == "disconnected"
        assert run_init(InitConfig(cwd=ws, graph="gortex", workspace="s")) == "disconnected"
        assert not (ws / ".gortex.yaml").exists()


# --------------------------------------------------------------------------- #
# AC-19
# --------------------------------------------------------------------------- #

OLDER_SHAPE = "workspace: x\n  cross_workspace_deps:\n    - workspace: y\n      module: z\n"


class TestAC19NeverOverwritten:
    """AC-19: an existing `.gortex.yaml` stays byte-identical; older shapes warn."""

    @pytest.mark.parametrize(("existing", "older"), [
        ("workspace: x\n", False),
        (OLDER_SHAPE, True),
    ])
    def test_rows(self, existing: str, older: bool, ws: Path, monkeypatch, capsys) -> None:
        """AC-19: example table rows."""
        gortex_on_path(monkeypatch, True)
        (ws / ".gortex.yaml").write_bytes(existing.encode("utf-8"))
        assert init_in(ws, monkeypatch, "--graph", "gortex", "--workspace", "s") == 0
        assert (ws / ".gortex.yaml").read_bytes() == existing.encode("utf-8")
        captured = capsys.readouterr()
        assert "gortex_config=exists" in captured.out.splitlines()
        assert ("older qr" in captured.err) is older
        if older:
            assert "delete" in captured.err.lower()

    def test_module_returns_exists(self, ws: Path, monkeypatch) -> None:
        """AC-19: _write_gortex_config returns "exists" and leaves the file alone."""
        gortex_on_path(monkeypatch, True)
        (ws / ".gortex.yaml").write_text("workspace: x\n", encoding="utf-8")
        assert _write_gortex_config(ws, "s", []) == "exists"
        assert (ws / ".gortex.yaml").read_text(encoding="utf-8") == "workspace: x\n"


# --------------------------------------------------------------------------- #
# AC-20
# --------------------------------------------------------------------------- #

class TestAC20NextStepsPrinted:
    """AC-20: next steps are printed on stderr for written/exists; no process is started."""

    @pytest.mark.parametrize(("status", "needles", "absent"), [
        ("written", ["gortex install --hook-mode=enrich", "gortex init --no-skills", "jdtls"],
         []),
        ("exists", ["gortex install --hook-mode=enrich"], []),
        ("disconnected", [], ["--hook-mode"]),
    ])
    def test_rows(self, status: str, needles: list[str], absent: list[str], ws: Path,
                  monkeypatch, capsys) -> None:
        """AC-20: example table rows, with subprocess and os.system patched to raise."""
        gortex_on_path(monkeypatch, status != "disconnected")
        if status == "exists":
            (ws / ".gortex.yaml").write_text("workspace: x\n", encoding="utf-8")
        block_processes(monkeypatch)
        assert init_in(ws, monkeypatch, "--graph", "gortex", "--workspace", "s") == 0
        captured = capsys.readouterr()
        assert f"gortex_config={status}" in captured.out.splitlines()
        for needle in needles:
            assert needle in captured.err
        for needle in absent:
            assert needle not in captured.err


# --------------------------------------------------------------------------- #
# AC-21
# --------------------------------------------------------------------------- #

class TestAC21ModuleCountMismatch:
    """AC-21: --module count neither 0 nor the --workspace-dep count exits 2, writes nothing."""

    @pytest.mark.parametrize(("argv", "exit_code"), [
        (["--graph", "gortex", "--workspace-dep", "a", "--workspace-dep", "b",
          "--module", "x"], 2),
        (["--graph", "gortex", "--module", "x"], 2),
        (["--graph", "gortex", "--workspace-dep", "a", "--module", "x"], 0),
    ])
    def test_rows(self, argv: list[str], exit_code: int, ws: Path, monkeypatch,
                  capsys) -> None:
        """AC-21: example table rows."""
        gortex_on_path(monkeypatch, True)
        assert init_in(ws, monkeypatch, *argv) == exit_code
        if exit_code == 2:
            assert "Error:" in capsys.readouterr().err
            assert list(ws.iterdir()) == []
        else:
            assert (ws / ".gortex.yaml").is_file()


# --------------------------------------------------------------------------- #
# AC-22
# --------------------------------------------------------------------------- #

SLUG_ROWS = [
    (["--graph", "gortex", "--workspace", "a: b"], 2),
    (["--graph", "gortex", "--workspace", 'x"\nmcp:'], 2),
    (["--graph", "gortex", "--workspace", "s", "--workspace-dep", "s"], 2),
    (["--graph", "gortex", "--workspace-dep", "a", "--module", "x y"], 2),
    (["--graph", "gortex", "--workspace", "edu-content.ingest_v2", "--workspace-dep", "a",
      "--module", "edu.acme:model/v2@1"], 0),
]


class TestAC22Validation:
    """AC-22: slugs and modules are validated before writing; failures exit 2."""

    @pytest.mark.parametrize(("argv", "exit_code"), SLUG_ROWS)
    def test_rows(self, argv: list[str], exit_code: int, ws: Path, monkeypatch,
                  capsys) -> None:
        """AC-22: example table rows."""
        gortex_on_path(monkeypatch, True)
        assert init_in(ws, monkeypatch, *argv) == exit_code
        if exit_code == 2:
            assert "Error:" in capsys.readouterr().err
            assert list(ws.iterdir()) == []
        else:
            loaded = loads((ws / ".gortex.yaml").read_text(encoding="utf-8"))
            assert loaded["workspace"] == "edu-content.ingest_v2"
            assert loaded["cross_workspace_deps"][0]["modules"] == ["edu.acme:model/v2@1"]

    def test_directory_name_with_space(self, tmp_path: Path, monkeypatch, capsys) -> None:
        """AC-22: directory `my repo`, gortex on PATH, no --workspace -> exit 2."""
        gortex_on_path(monkeypatch, True)
        repo = tmp_path / "my repo"
        repo.mkdir()
        assert init_in(repo, monkeypatch, "--graph", "gortex") == 2
        assert "Error:" in capsys.readouterr().err
        assert list(repo.iterdir()) == []

    def test_run_init_raises_init_error(self, ws: Path, monkeypatch) -> None:
        """AC-22: invalid input raises InitError(ValueError) before anything is written."""
        from quality_router.init import InitError

        assert issubclass(InitError, ValueError)
        gortex_on_path(monkeypatch, True)
        with pytest.raises(InitError):
            run_init(InitConfig(cwd=ws, graph="gortex", workspace="a: b"))
        assert list(ws.iterdir()) == []


# --------------------------------------------------------------------------- #
# AC-23
# --------------------------------------------------------------------------- #

class TestAC23SilentWithoutGraph:
    """AC-23: without --graph gortex no `.gortex.yaml` and no `gortex_config=` line."""

    @pytest.mark.parametrize("argv", [[], ["--host", "cursor"]])
    def test_rows(self, argv: list[str], ws: Path, monkeypatch, capsys) -> None:
        """AC-23: example table rows (gortex on PATH)."""
        gortex_on_path(monkeypatch, True)
        assert init_in(ws, monkeypatch, *argv) == 0
        assert not (ws / ".gortex.yaml").exists()
        assert "gortex_config=" not in capsys.readouterr().out

    def test_run_init_returns_none(self, ws: Path, monkeypatch) -> None:
        """AC-23: run_init returns None without --graph gortex."""
        gortex_on_path(monkeypatch, True)
        assert run_init(InitConfig(cwd=ws)) is None
