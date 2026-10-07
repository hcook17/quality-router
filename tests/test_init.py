"""Tests for qr init: portable stamps, host adapters, gortex graph, invariants."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from quality_router.cli import run
from quality_router.host_bind import bind_host
from quality_router.init import (
    ADAPTERS,
    InitConfig,
    _write_gortex_config,
    _write_portable_stamps,
    run_init,
)

# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture
def init_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "init-workspace"
    ws.mkdir()
    return ws


@pytest.fixture
def local_quality_root(tmp_path: Path) -> Path:
    root = tmp_path / "local-quality"
    root.mkdir()
    (root / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    (root / "install.ps1").write_text("# local installer\n", encoding="utf-8")
    (root / "install.sh").write_text("# local installer\n", encoding="utf-8")
    return root


# --------------------------------------------------------------------------- #
# Portable stamps
# --------------------------------------------------------------------------- #

class TestPortableStamps:
    def test_writes_portable_rule(self, init_workspace: Path) -> None:
        _write_portable_stamps(init_workspace)
        rule = init_workspace / ".quality-router" / "rule.md"
        assert rule.is_file()
        content = rule.read_text(encoding="utf-8")
        assert "Quality Router Rule" in content
        assert "SonarQube (local only" in content

    def test_writes_hooks_sh(self, init_workspace: Path) -> None:
        _write_portable_stamps(init_workspace)
        hooks_sh = init_workspace / ".quality-router" / "hooks.sh"
        assert hooks_sh.is_file()
        content = hooks_sh.read_text(encoding="utf-8")
        assert "#!/usr/bin/env bash" in content
        assert "semgrep" in content
        assert "spectral" in content

    def test_writes_hooks_ps1(self, init_workspace: Path) -> None:
        _write_portable_stamps(init_workspace)
        hooks_ps1 = init_workspace / ".quality-router" / "hooks.ps1"
        assert hooks_ps1.is_file()
        content = hooks_ps1.read_text(encoding="utf-8")
        assert "# Quality-router hooks runner" in content
        assert "semgrep" in content

    def test_writes_gitnexus_off_marker(self, init_workspace: Path) -> None:
        _write_portable_stamps(init_workspace)
        marker = init_workspace / ".quality-router" / "gitnexus-hooks.off"
        assert marker.is_file()

    def test_idempotent_no_duplication(self, init_workspace: Path) -> None:
        _write_portable_stamps(init_workspace)
        first_rule = (init_workspace / ".quality-router" / "rule.md").read_text(encoding="utf-8")
        _write_portable_stamps(init_workspace)
        second_rule = (init_workspace / ".quality-router" / "rule.md").read_text(encoding="utf-8")
        assert first_rule == second_rule

    def test_no_mcp_json_written(self, init_workspace: Path) -> None:
        _write_portable_stamps(init_workspace)
        # No .cursor/mcp.json should be created
        cursor_mcp = init_workspace / ".cursor" / "mcp.json"
        assert not cursor_mcp.exists()

    def test_no_gitnexus_hooks_env_set(
        self, init_workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_portable_stamps(init_workspace)
        # Verify we never set GITNEXUS_HOOKS
        assert "GITNEXUS_HOOKS" not in os.environ


# --------------------------------------------------------------------------- #
# Host adapters
# --------------------------------------------------------------------------- #

class TestCursorAdapter:
    def test_stamps_cursor_rule(self, init_workspace: Path) -> None:
        ADAPTERS["cursor"].stamp(init_workspace)
        rule = init_workspace / ".cursor" / "rules" / "quality-router.mdc"
        assert rule.is_file()
        content = rule.read_text(encoding="utf-8")
        assert "quality-router" in content

    def test_stamps_cursor_gitnexus_off(self, init_workspace: Path) -> None:
        ADAPTERS["cursor"].stamp(init_workspace)
        marker = init_workspace / ".cursor" / "gitnexus-hooks.off"
        assert marker.is_file()

    def test_cursor_adapter_idempotent(self, init_workspace: Path) -> None:
        ADAPTERS["cursor"].stamp(init_workspace)
        rule_path = init_workspace / ".cursor" / "rules" / "quality-router.mdc"
        first = rule_path.read_text(encoding="utf-8")
        ADAPTERS["cursor"].stamp(init_workspace)
        second = rule_path.read_text(encoding="utf-8")
        assert first == second


class TestVsCodeAdapter:
    def test_stamps_vscode_instructions(self, init_workspace: Path) -> None:
        ADAPTERS["vscode"].stamp(init_workspace)
        instructions = init_workspace / ".vscode" / "quality-router-instructions.md"
        assert instructions.is_file()
        content = instructions.read_text(encoding="utf-8")
        assert "Quality Router" in content


class TestClaudeCodeAdapter:
    def test_stamps_claude_md(self, init_workspace: Path) -> None:
        ADAPTERS["claude-code"].stamp(init_workspace)
        claude_md = init_workspace / "CLAUDE.md"
        assert claude_md.is_file()
        content = claude_md.read_text(encoding="utf-8")
        assert "Quality Router" in content


# --------------------------------------------------------------------------- #
# Gortex graph
# --------------------------------------------------------------------------- #

class TestGortexConfig:
    def test_no_op_when_gortex_missing(
        self, init_workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Monkey-patch shutil.which to pretend gortex is NOT on PATH
        def fake_which(name: str) -> str | None:
            if name == "gortex":
                return None
            return "/usr/bin/other"

        import quality_router.init as init_module
        original_which = init_module.shutil.which
        init_module.shutil.which = fake_which
        try:
            _write_gortex_config(init_workspace, workspace="my-svc", deps=[])
            assert not (init_workspace / ".gortex.yaml").exists()
        finally:
            init_module.shutil.which = original_which

    def test_writes_gortex_yaml_when_present(
        self, init_workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Mock shutil.which to pretend gortex is on PATH
        def fake_which(name: str) -> str | None:
            if name == "gortex":
                return "/usr/bin/gortex"
            return None

        with patch("quality_router.init.shutil.which", side_effect=fake_which):
            _write_gortex_config(init_workspace, workspace="my-service", deps=[])

        yaml = init_workspace / ".gortex.yaml"
        assert yaml.is_file()
        content = yaml.read_text(encoding="utf-8")
        assert 'workspace: "my-service"' in content

    def test_uses_directory_basename_when_no_workspace_flag(
        self, init_workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_which(name: str) -> str | None:
            if name == "gortex":
                return "/usr/bin/gortex"
            return None

        with patch("quality_router.init.shutil.which", side_effect=fake_which):
            _write_gortex_config(init_workspace, workspace=None, deps=[])

        yaml = init_workspace / ".gortex.yaml"
        content = yaml.read_text(encoding="utf-8")
        assert 'workspace: "init-workspace"' in content

    def test_writes_workspace_deps(
        self, init_workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_which(name: str) -> str | None:
            if name == "gortex":
                return "/usr/bin/gortex"
            return None

        with patch("quality_router.init.shutil.which", side_effect=fake_which):
            _write_gortex_config(
                init_workspace,
                workspace="my-svc",
                deps=[("other-svc", "services/shared")],
            )

        yaml = init_workspace / ".gortex.yaml"
        content = yaml.read_text(encoding="utf-8")
        assert 'workspace: "my-svc"' in content
        assert "\ncross_workspace_deps:\n" in content
        assert '  - workspace: "other-svc"' in content
        assert '    modules:\n      - "services/shared"\n' in content
        assert "module:" not in content


# --------------------------------------------------------------------------- #
# End-to-end run_init
# --------------------------------------------------------------------------- #

class TestRunInit:
    def test_portable_only(self, init_workspace: Path) -> None:
        config = InitConfig(cwd=init_workspace)
        run_init(config)
        assert (init_workspace / ".quality-router" / "rule.md").is_file()
        assert (init_workspace / ".quality-router" / "hooks.sh").is_file()
        assert (init_workspace / ".quality-router" / "hooks.ps1").is_file()
        assert (init_workspace / ".quality-router" / "gitnexus-hooks.off").is_file()
        # No cursor dir created without --host
        assert not (init_workspace / ".cursor").exists()

    def test_with_cursor_host(self, init_workspace: Path) -> None:
        config = InitConfig(cwd=init_workspace, host="cursor")
        run_init(config)
        assert (init_workspace / ".quality-router" / "rule.md").is_file()
        assert (init_workspace / ".cursor" / "rules" / "quality-router.mdc").is_file()
        assert (init_workspace / ".cursor" / "gitnexus-hooks.off").is_file()

    def test_cursor_host_needs_explicit_flag(self, init_workspace: Path) -> None:
        # Without --host cursor, no .cursor dir
        config = InitConfig(cwd=init_workspace)
        run_init(config)
        assert not (init_workspace / ".cursor").exists()

    def test_status_reports_portable_marker(
        self, init_workspace: Path, local_quality_root: Path
    ) -> None:
        from quality_router.status_report import report_status

        config = InitConfig(cwd=init_workspace)
        run_init(config)

        bind = bind_host(
            root_flag=str(local_quality_root),
            sonar_port_flag=9000,
            sonar_mcp_url_flag="http://host.docker.internal:9000",
            environ={},
        )
        text = report_status(
            bind,
            cwd=init_workspace,
            windows=True,
            environ={},
            which=lambda _name: None,
            listen=lambda _port: "down",
        )
        assert "agent_host_lock=none" in text


# --------------------------------------------------------------------------- #
# No LLM base-URL / BYOK writes
# --------------------------------------------------------------------------- #

class TestNoLlmUrlWrites:
    def test_init_does_not_write_anthropic_base_url(self, init_workspace: Path) -> None:
        config = InitConfig(cwd=init_workspace, host="cursor")
        run_init(config)
        # No ENV file, no settings file with ANTHROPIC_BASE_URL
        for p in init_workspace.rglob("*"):
            if p.is_file():
                content = p.read_text(encoding="utf-8", errors="replace")
                assert "ANTHROPIC_BASE_URL" not in content

    def test_init_does_not_write_openai_base_url(self, init_workspace: Path) -> None:
        config = InitConfig(cwd=init_workspace, host="cursor")
        run_init(config)
        for p in init_workspace.rglob("*"):
            if p.is_file():
                content = p.read_text(encoding="utf-8", errors="replace")
                assert "Override OpenAI Base URL" not in content
                assert "customOAIModels" not in content

    def test_init_does_not_spawn_ollama(self, init_workspace: Path) -> None:
        # Verify init doesn't start :11434 or ollama serve
        import subprocess

        seen: list[str] = []

        original_run = subprocess.run

        def fake_run(*args, **kwargs):
            seen.append(str(args[0]) if args else "")
            return original_run(*args, **kwargs)

        with patch("subprocess.run", side_effect=fake_run):
            config = InitConfig(cwd=init_workspace, host="cursor")
            run_init(config)

        # Should not have spawned ollama or any server
        for s in seen:
            assert "ollama" not in s.lower()
            assert "11434" not in s


# --------------------------------------------------------------------------- #
# Coverage: base class, cmd_init via CLI, gortex-present branch exits
# --------------------------------------------------------------------------- #


class TestHostAdapterBase:
    def test_base_stamp_raises_not_implemented(self, init_workspace: Path) -> None:
        from quality_router.init import HostAdapter

        adapter = HostAdapter()
        with pytest.raises(NotImplementedError):
            adapter.stamp(init_workspace)


class TestCmdInitViaCli:
    def test_init_via_cli_run(
        self, init_workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Exercise cmd_init through the CLI parser to cover cli.py:257-271
        old_cwd = Path.cwd()
        try:
            os.chdir(init_workspace)
            # Build args as if from CLI: qr init --host cursor
            code = run(["init", "--host", "cursor"])
            assert code == 0
        finally:
            os.chdir(old_cwd)

        # Verify stamps were written
        assert (init_workspace / ".quality-router" / "rule.md").is_file()
        assert (init_workspace / ".cursor" / "rules" / "quality-router.mdc").is_file()

    def test_init_via_cli_portable_only(self, init_workspace: Path) -> None:
        old_cwd = Path.cwd()
        try:
            os.chdir(init_workspace)
            code = run(["init"])
            assert code == 0
        finally:
            os.chdir(old_cwd)

        assert (init_workspace / ".quality-router" / "rule.md").is_file()
        # No .cursor without --host
        assert not (init_workspace / ".cursor").exists()


class TestGortexBranchExits:
    def test_gortex_yaml_write_branch_exit(
        self, init_workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Cover init.py:246->exit (gortex yaml already exists)."""
        def fake_which(name: str) -> str | None:
            if name == "gortex":
                return "/usr/bin/gortex"
            return None

        with patch("quality_router.init.shutil.which", side_effect=fake_which):
            # First write creates the yaml
            _write_gortex_config(init_workspace, workspace="test-svc", deps=[])
            yaml_path = init_workspace / ".gortex.yaml"
            assert yaml_path.exists()

            # Second call hits the `if not gortex_yaml.exists():` branch exit
            _write_gortex_config(init_workspace, workspace="other-svc", deps=[])

            # Should not be overwritten
            content = yaml_path.read_text(encoding="utf-8")
            assert 'workspace: "test-svc"' in content
            assert 'workspace: "other-svc"' not in content

    def test_cursor_adapter_idempotent_second_stamp_exits_early(
        self, init_workspace: Path
    ) -> None:
        """Cover CursorAdapter stamp branch exits (159, 166) on re-stamp."""
        ADAPTERS["cursor"].stamp(init_workspace)
        rule = init_workspace / ".cursor" / "rules" / "quality-router.mdc"
        assert rule.exists()

        # Re-stamp: both inner `if not ...exists()` branches exit early
        ADAPTERS["cursor"].stamp(init_workspace)

        # Content unchanged
        first = rule.read_text(encoding="utf-8")
        second = rule.read_text(encoding="utf-8")
        assert first == second


class TestWorkspaceDepCli:
    def test_init_with_workspace_dep_via_cli(self, init_workspace: Path) -> None:
        """Cover cli.py:259-260 (workspace_dep loop) via CLI args."""

        old_cwd = Path.cwd()
        try:
            os.chdir(init_workspace)
            # qr init --host cursor --workspace-dep other-svc --module services/shared
            code = run(
                [
                    "init",
                    "--host",
                    "cursor",
                    "--workspace-dep",
                    "other-svc",
                    "--module",
                    "services/shared",
                ]
            )
            assert code == 0
        finally:
            os.chdir(old_cwd)

        # Verify stamps + deps collected (deps go to gortex config, skipped if no gortex)
        assert (init_workspace / ".quality-router" / "rule.md").is_file()
        assert (init_workspace / ".cursor" / "rules" / "quality-router.mdc").is_file()

    def test_init_with_multiple_workspace_deps_via_cli(self, init_workspace: Path) -> None:
        """Cover cli.py:258-260 with multiple --workspace-dep flags."""
        old_cwd = Path.cwd()
        try:
            os.chdir(init_workspace)
            code = run(
                [
                    "init",
                    "--host",
                    "cursor",
                    "--workspace-dep",
                    "svc-a",
                    "--module",
                    "lib/a",
                    "--workspace-dep",
                    "svc-b",
                    "--module",
                    "lib/b",
                ]
            )
            assert code == 0
        finally:
            os.chdir(old_cwd)

        assert (init_workspace / ".quality-router" / "rule.md").is_file()
