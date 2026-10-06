"""Held-out tests for phase 6 section B, `qr init --graph gortex` (AC-15 .. AC-23).

Self-contained: imports only pytest, the stdlib and quality_router.*.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from quality_router.cli import run
from quality_router.harness.yamlsubset import loads
from quality_router.init import InitConfig, _write_gortex_config, run_init

HEAD = (
    "# Written by `qr init --graph gortex`. qr never overwrites this file.\n"
    "# Settings follow research/harness-kb/implementations.md (quality-router):\n"
    "#   embedding off: embedding indexes are poisonable and localize Java poorly\n"
    "#   facade-v1 in hide mode: about 15 inlined tools still select well\n"
    "#   Java Kafka boundaries declared: Gortex does not detect them for Java\n"
)
TAIL = (
    "embedding:\n"
    "  enabled: false\n"
    "mcp:\n"
    "  tools:\n"
    "    preset: facade-v1\n"
    "    mode: hide\n"
    "index:\n"
    "  event_bus:\n"
    "    - name: kafka\n"
    "      type: producer\n"
    "      callee: kafkaTemplate.send\n"
    '      topic_arg: "0"\n'
    "    - name: kafka\n"
    "      type: consumer\n"
    "      decorator: KafkaListener\n"
    "      topic_arg: topics\n"
)


def expected(workspace: str, deps: list[tuple[str, list[str]]] | None = None) -> str:
    block = ""
    if deps:
        block = "cross_workspace_deps:\n"
        for name, modules in deps:
            block += f'  - workspace: "{name}"\n    modules:\n'
            block += "".join(f'      - "{m}"\n' for m in modules)
            block += "    mode: read-only\n"
    return HEAD + f'workspace: "{workspace}"\n' + block + TAIL


def on_path(monkeypatch, present: bool) -> None:
    def which(name, *_a, **_k):
        return "/opt/homebrew/bin/gortex" if present and name == "gortex" else None

    monkeypatch.setattr("quality_router.init.shutil.which", which)


def qr(*argv: str) -> int:
    try:
        return run(list(argv))
    except SystemExit as exc:
        if exc.code is None:
            return 0
        return exc.code if isinstance(exc.code, int) else 2


def init(where: Path, monkeypatch, *argv: str) -> int:
    monkeypatch.chdir(where)
    return qr("init", *argv)


def no_processes(monkeypatch) -> None:
    def boom(*_a, **_k):
        raise AssertionError("qr init must not start a process")

    for name in ("run", "Popen", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, boom)
    for name in ("system", "popen", "posix_spawn", "posix_spawnp", "execv", "execvp"):
        if hasattr(os, name):
            monkeypatch.setattr(os, name, boom)


def text(where: Path) -> str:
    return (where / ".gortex.yaml").read_text(encoding="utf-8")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "lms-catalog"
    path.mkdir()
    return path


# ----------------------------------------------------------------------------- #
# AC-15
# ----------------------------------------------------------------------------- #

def test_ac15_slug_with_dots_and_underscores(repo, monkeypatch, capsys):
    """AC-15: exact text with a different workspace slug."""
    on_path(monkeypatch, True)
    assert init(repo, monkeypatch, "--graph", "gortex", "--workspace",
                "lms.content_ingest-2") == 0
    assert text(repo) == expected("lms.content_ingest-2")
    out = capsys.readouterr().out.splitlines()
    assert out.count("gortex_config=written") == 1


def test_ac15_directory_name_default(tmp_path, monkeypatch):
    """AC-15: workspace defaults to the directory name."""
    on_path(monkeypatch, True)
    where = tmp_path / "Catalog_Service.v2"
    where.mkdir()
    assert init(where, monkeypatch, "--graph", "gortex") == 0
    assert text(where) == expected("Catalog_Service.v2")


def test_ac15_host_flag_does_not_change_the_file(repo, monkeypatch):
    """AC-15: a host adapter alongside --graph gortex writes the same text."""
    on_path(monkeypatch, True)
    assert init(repo, monkeypatch, "--graph", "gortex", "--host", "claude-code",
                "--workspace", "roster") == 0
    assert text(repo) == expected("roster")


def test_ac15_run_init_uses_directory_name(repo, monkeypatch):
    """AC-15: run_init with workspace None uses the directory name and returns written."""
    on_path(monkeypatch, True)
    assert run_init(InitConfig(cwd=repo, graph="gortex")) == "written"
    assert text(repo) == expected("lms-catalog")


# ----------------------------------------------------------------------------- #
# AC-16
# ----------------------------------------------------------------------------- #

def test_ac16_interleaved_merge_exact_text(repo, monkeypatch):
    """AC-16: entries in first-seen order, modules merged in first-seen order, no dups."""
    on_path(monkeypatch, True)
    assert init(repo, monkeypatch, "--graph", "gortex", "--workspace", "lms-catalog",
                "--workspace-dep", "roster", "--module", "org.lms:roster-api",
                "--workspace-dep", "grading", "--module", "org.lms:grading-events",
                "--workspace-dep", "roster", "--module", "org.lms:roster-events",
                "--workspace-dep", "grading", "--module", "org.lms:grading-events",
                "--workspace-dep", "media", "--module", "libs/media") == 0
    assert text(repo) == expected("lms-catalog", [
        ("roster", ["org.lms:roster-api", "org.lms:roster-events"]),
        ("grading", ["org.lms:grading-events"]),
        ("media", ["libs/media"]),
    ])


def test_ac16_pairing_is_by_position(repo, monkeypatch):
    """AC-16: --module pairs with --workspace-dep by position, not adjacency."""
    on_path(monkeypatch, True)
    assert init(repo, monkeypatch, "--graph", "gortex", "--workspace", "w",
                "--module", "m1", "--module", "m2",
                "--workspace-dep", "d1", "--workspace-dep", "d2") == 0
    assert loads(text(repo))["cross_workspace_deps"] == [
        {"workspace": "d1", "modules": ["m1"], "mode": "read-only"},
        {"workspace": "d2", "modules": ["m2"], "mode": "read-only"},
    ]


def test_ac16_repeated_dep_without_modules(repo, monkeypatch):
    """AC-16: the same dependency twice with zero --module is one entry with `.`."""
    on_path(monkeypatch, True)
    assert init(repo, monkeypatch, "--graph", "gortex", "--workspace", "w",
                "--workspace-dep", "roster", "--workspace-dep", "grading",
                "--workspace-dep", "roster") == 0
    assert text(repo) == expected("w", [("roster", ["."]), ("grading", ["."])])


# ----------------------------------------------------------------------------- #
# AC-17
# ----------------------------------------------------------------------------- #

def test_ac17_numeric_and_keyword_values_stay_strings(repo, monkeypatch):
    """AC-17: quoted values load as strings even when they look like numbers or keywords."""
    on_path(monkeypatch, True)
    assert init(repo, monkeypatch, "--graph", "gortex", "--workspace", "123",
                "--workspace-dep", "true", "--module", "1.0",
                "--workspace-dep", "null", "--module", "@scope/pkg:1.0-rc_2") == 0
    loaded = loads(text(repo))
    assert loaded["workspace"] == "123"
    assert loaded["cross_workspace_deps"] == [
        {"workspace": "true", "modules": ["1.0"], "mode": "read-only"},
        {"workspace": "null", "modules": ["@scope/pkg:1.0-rc_2"], "mode": "read-only"},
    ]
    assert loaded["mcp"] == {"tools": {"preset": "facade-v1", "mode": "hide"}}
    assert loaded["embedding"] == {"enabled": False}
    assert loaded["index"]["event_bus"][0]["topic_arg"] == "0"
    assert list(loaded) == ["workspace", "cross_workspace_deps", "embedding", "mcp", "index"]


def test_ac17_run_init_deterministic(tmp_path, monkeypatch):
    """AC-17: the same InitConfig in two directories produces identical bytes."""
    on_path(monkeypatch, True)
    outs = []
    for name in ("x1", "x2"):
        where = tmp_path / name
        where.mkdir()
        cfg = InitConfig(cwd=where, graph="gortex", workspace="lms",
                         workspace_deps=[("roster", "org.lms:roster-api")])
        assert run_init(cfg) == "written"
        outs.append((where / ".gortex.yaml").read_bytes())
    assert outs[0] == outs[1]
    assert b"\t" not in outs[0]
    assert b"\r" not in outs[0]
    assert "cross_workspace_deps" in loads(outs[0].decode("utf-8"))


def test_ac17_no_flow_collections(repo, monkeypatch):
    """AC-17: block style only."""
    on_path(monkeypatch, True)
    assert init(repo, monkeypatch, "--graph", "gortex", "--workspace", "w",
                "--workspace-dep", "a", "--module", "x") == 0
    for line in text(repo).splitlines():
        if line.lstrip().startswith("#"):
            continue
        assert "[" not in line and "{" not in line


# ----------------------------------------------------------------------------- #
# AC-18
# ----------------------------------------------------------------------------- #

def test_ac18_disconnected_with_deps(repo, monkeypatch, capsys):
    """AC-18: without gortex nothing is written even with dependencies; status line once."""
    on_path(monkeypatch, False)
    assert init(repo, monkeypatch, "--graph", "gortex", "--workspace", "w",
                "--workspace-dep", "roster", "--module", "org.lms:roster-api") == 0
    assert not (repo / ".gortex.yaml").exists()
    cap = capsys.readouterr()
    assert cap.out.splitlines().count("gortex_config=disconnected") == 1
    assert "gortex not on PATH" in cap.err
    assert "brew install zzet/tap/gortex" in cap.err
    for bad in ("curl", "| sh", "irm"):
        assert bad not in cap.err
        assert bad not in cap.out


def test_ac18_run_init_disconnected_with_deps(repo, monkeypatch):
    """AC-18: run_init returns disconnected and writes no `.gortex.yaml`."""
    on_path(monkeypatch, False)
    cfg = InitConfig(cwd=repo, graph="gortex", workspace="w",
                     workspace_deps=[("roster", "libs/roster")])
    assert run_init(cfg) == "disconnected"
    assert not (repo / ".gortex.yaml").exists()


# ----------------------------------------------------------------------------- #
# AC-19
# ----------------------------------------------------------------------------- #

@pytest.mark.parametrize(("existing", "older"), [
    ('workspace: "lms"\ncross_workspace_deps:\n  - workspace: "roster"\n    module: "x"\n'
     "    mode: read-only\n", True),
    ("# Gortex workspace (quality-router constituent)\nworkspace: lms\n"
     "  cross_workspace_deps:\n    - workspace: roster\n      modules: x\n", True),
    (expected("lms", [("roster", ["org.lms:roster-api"])]), False),
    ("workspace: lms\nembedding:\n  enabled: true\n", False),
])
def test_ac19_older_shape_detection(existing, older, repo, monkeypatch, capsys):
    """AC-19: `module:` key or an indented cross_workspace_deps line warns; new shape does not."""
    on_path(monkeypatch, True)
    (repo / ".gortex.yaml").write_bytes(existing.encode("utf-8"))
    assert init(repo, monkeypatch, "--graph", "gortex", "--workspace", "other") == 0
    assert (repo / ".gortex.yaml").read_bytes() == existing.encode("utf-8")
    cap = capsys.readouterr()
    assert "gortex_config=exists" in cap.out.splitlines()
    assert ("older qr" in cap.err) is older


def test_ac19_rerun_is_exists_and_identical(repo, monkeypatch, capsys):
    """AC-19: a second run keeps the file qr wrote, reports exists, no older-qr warning."""
    on_path(monkeypatch, True)
    assert init(repo, monkeypatch, "--graph", "gortex", "--workspace", "lms",
                "--workspace-dep", "roster") == 0
    first = (repo / ".gortex.yaml").read_bytes()
    capsys.readouterr()
    assert init(repo, monkeypatch, "--graph", "gortex", "--workspace", "changed") == 0
    assert (repo / ".gortex.yaml").read_bytes() == first
    cap = capsys.readouterr()
    assert "gortex_config=exists" in cap.out.splitlines()
    assert "older qr" not in cap.err


def test_ac19_module_api_does_not_touch(repo, monkeypatch):
    """AC-19: _write_gortex_config on an older file returns exists and keeps the bytes."""
    on_path(monkeypatch, True)
    old = "workspace: lms\n  cross_workspace_deps:\n    - workspace: r\n      module: m\n"
    (repo / ".gortex.yaml").write_text(old, encoding="utf-8")
    assert _write_gortex_config(repo, "lms", [("r", "m")]) == "exists"
    assert text(repo) == old


# ----------------------------------------------------------------------------- #
# AC-20
# ----------------------------------------------------------------------------- #

NEXT = ("gortex install --hook-mode=enrich", "gortex init --no-skills", "jdtls")


@pytest.mark.parametrize("status", ["written", "exists"])
def test_ac20_all_next_steps_for_written_and_exists(status, repo, monkeypatch, capsys):
    """AC-20: written and exists both list all three next steps; nothing is spawned."""
    on_path(monkeypatch, True)
    if status == "exists":
        (repo / ".gortex.yaml").write_text("workspace: lms\n", encoding="utf-8")
    no_processes(monkeypatch)
    assert init(repo, monkeypatch, "--graph", "gortex", "--workspace", "lms",
                "--workspace-dep", "roster", "--module", "org.lms:roster-api") == 0
    cap = capsys.readouterr()
    for needle in NEXT:
        assert needle in cap.err
    assert f"gortex_config={status}" in cap.out.splitlines()


def test_ac20_disconnected_prints_no_gortex_commands(repo, monkeypatch, capsys):
    """AC-20: disconnected lists no hook-mode or gortex init step and spawns nothing."""
    on_path(monkeypatch, False)
    no_processes(monkeypatch)
    assert init(repo, monkeypatch, "--graph", "gortex", "--host", "cursor") == 0
    cap = capsys.readouterr()
    assert "--hook-mode" not in cap.err
    assert "gortex init --no-skills" not in cap.err


# ----------------------------------------------------------------------------- #
# AC-21
# ----------------------------------------------------------------------------- #

@pytest.mark.parametrize(("argv", "present"), [
    (["--workspace-dep", "a", "--workspace-dep", "b", "--workspace-dep", "c",
      "--module", "x", "--module", "y"], True),
    (["--workspace-dep", "a", "--module", "x", "--module", "y"], True),
    (["--module", "x", "--module", "y"], True),
    (["--workspace-dep", "a", "--workspace-dep", "b", "--module", "x"], False),
    (["--module", "x"], False),
])
def test_ac21_mismatch_exits_2_and_writes_nothing(argv, present, repo, monkeypatch, capsys):
    """AC-21: count mismatches exit 2, `Error:` on stderr, nothing written."""
    on_path(monkeypatch, present)
    assert init(repo, monkeypatch, "--graph", "gortex", "--workspace", "lms", *argv) == 2
    assert "Error:" in capsys.readouterr().err
    assert list(repo.iterdir()) == []


def test_ac21_matching_counts_pass(repo, monkeypatch):
    """AC-21: two deps with two modules is fine."""
    on_path(monkeypatch, True)
    assert init(repo, monkeypatch, "--graph", "gortex", "--workspace", "lms",
                "--workspace-dep", "a", "--workspace-dep", "b",
                "--module", "x", "--module", "y") == 0
    assert (repo / ".quality-router").is_dir()


# ----------------------------------------------------------------------------- #
# AC-22
# ----------------------------------------------------------------------------- #

@pytest.mark.parametrize("argv", [
    ["--workspace", "lms", "--workspace-dep", "core/lib"],
    ["--workspace", "lms", "--workspace-dep", "_core"],
    ["--workspace", "lms", "--workspace-dep=-core"],
    ["--workspace", ".hidden"],
    ["--workspace", "lms svc"],
    ["--workspace", "lms", "--workspace-dep", "a", "--module", 'x"y'],
    ["--workspace", "lms", "--workspace-dep", "a", "--module", ""],
    ["--workspace", "lms", "--workspace-dep", "a", "--module", "a,b"],
    ["--workspace", "lms", "--workspace-dep", "a", "--module", "x\ny"],
    ["--workspace", "lms", "--workspace-dep", "a", "--workspace-dep", "lms"],
])
@pytest.mark.parametrize("present", [True, False])
def test_ac22_invalid_input(argv, present, repo, monkeypatch, capsys):
    """AC-22: invalid slugs/modules/self-dependency exit 2 whether or not gortex is on PATH."""
    on_path(monkeypatch, present)
    assert init(repo, monkeypatch, "--graph", "gortex", *argv) == 2
    assert "Error:" in capsys.readouterr().err
    assert list(repo.iterdir()) == []


def test_ac22_dependency_equal_to_directory_workspace(tmp_path, monkeypatch, capsys):
    """AC-22: with no --workspace, a dependency equal to the directory name is an error."""
    on_path(monkeypatch, True)
    where = tmp_path / "catalog"
    where.mkdir()
    assert init(where, monkeypatch, "--graph", "gortex", "--workspace-dep", "catalog") == 2
    assert "Error:" in capsys.readouterr().err
    assert list(where.iterdir()) == []


def test_ac22_bad_directory_name_ok_when_disconnected(tmp_path, monkeypatch, capsys):
    """AC-22: the directory-name rule applies only when gortex is on PATH."""
    on_path(monkeypatch, False)
    where = tmp_path / "my repo"
    where.mkdir()
    assert init(where, monkeypatch, "--graph", "gortex") == 0
    assert "gortex_config=disconnected" in capsys.readouterr().out.splitlines()


def test_ac22_bad_directory_name_ok_with_workspace_flag(tmp_path, monkeypatch):
    """AC-22: --workspace replaces the directory name, so the directory is not checked."""
    on_path(monkeypatch, True)
    where = tmp_path / "my repo"
    where.mkdir()
    assert init(where, monkeypatch, "--graph", "gortex", "--workspace", "my-repo") == 0
    assert text(where) == expected("my-repo")


@pytest.mark.parametrize("argv", [
    ["--workspace", "A"],
    ["--workspace", "9lives", "--workspace-dep", "Roster.API_v2", "--module",
     "@lms/roster:2.0.0-rc_1"],
])
def test_ac22_valid_edges(argv, repo, monkeypatch):
    """AC-22: single-character and mixed-character slugs and modules are accepted."""
    on_path(monkeypatch, True)
    assert init(repo, monkeypatch, "--graph", "gortex", *argv) == 0
    assert (repo / ".gortex.yaml").is_file()


@pytest.mark.parametrize("cfg_kwargs", [
    {"workspace": "lms", "workspace_deps": [("bad slug", "x")]},
    {"workspace": "lms", "workspace_deps": [("roster", "has space")]},
    {"workspace": "lms", "workspace_deps": [("lms", "x")]},
])
@pytest.mark.parametrize("present", [True, False])
def test_ac22_run_init_raises_before_writing(cfg_kwargs, present, repo, monkeypatch):
    """AC-22: run_init raises InitError before anything is written, PATH or not."""
    from quality_router.init import InitError

    on_path(monkeypatch, present)
    with pytest.raises(InitError):
        run_init(InitConfig(cwd=repo, graph="gortex", **cfg_kwargs))
    assert list(repo.iterdir()) == []


def test_ac22_run_init_bad_directory_name(tmp_path, monkeypatch):
    """AC-22: run_init with no workspace and a bad directory name raises when gortex is on PATH."""
    from quality_router.init import InitError

    on_path(monkeypatch, True)
    where = tmp_path / "my repo"
    where.mkdir()
    with pytest.raises(InitError):
        run_init(InitConfig(cwd=where, graph="gortex"))
    assert list(where.iterdir()) == []


# ----------------------------------------------------------------------------- #
# AC-23
# ----------------------------------------------------------------------------- #

@pytest.mark.parametrize("argv", [
    ["--host", "vscode"],
    ["--policy"],
    ["--host", "claude-code", "--workspace-dep", "roster", "--module", "libs/roster"],
])
def test_ac23_no_graph_is_silent(argv, repo, monkeypatch, capsys):
    """AC-23: without --graph gortex there is no file and no gortex_config= line."""
    on_path(monkeypatch, True)
    assert init(repo, monkeypatch, *argv) == 0
    assert not (repo / ".gortex.yaml").exists()
    cap = capsys.readouterr()
    assert "gortex_config=" not in cap.out
    assert "gortex_config=" not in cap.err


def test_ac23_run_init_none_with_host(repo, monkeypatch):
    """AC-23: run_init returns None without graph, even with deps and gortex on PATH."""
    on_path(monkeypatch, True)
    cfg = InitConfig(cwd=repo, host="cursor", workspace="lms",
                     workspace_deps=[("roster", "libs/roster")])
    assert run_init(cfg) is None
    assert not (repo / ".gortex.yaml").exists()
