"""Wrap local-quality install.ps1 / install.sh. Never irm|iex."""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

from quality_router.host_bind import HostBind, assert_local_sonar_url

REMOTE_PIPE_MARKERS = ("irm |", "| iex", "invoke-expression", "invoke-restmethod")


def build_installer_argv(
    bind: HostBind,
    *,
    reset_volume: bool,
    skip_bootstrap: bool,
    windows: bool,
) -> list[str]:
    script = bind.installer_script(windows=windows)
    _require_installer_files(bind, script)
    if windows:
        argv = _windows_argv(script, bind, reset_volume, skip_bootstrap)
    else:
        argv = _posix_argv(script, bind, reset_volume, skip_bootstrap)
    refuse_remote_pipe(argv)
    return argv


def refuse_remote_pipe(argv: Sequence[str]) -> None:
    joined = " ".join(argv).lower()
    for marker in REMOTE_PIPE_MARKERS:
        if marker in joined:
            raise ValueError("refusing irm|iex installer invocation")


def invoke_installer(
    argv: Sequence[str],
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> int:
    refuse_remote_pipe(argv)
    run = runner if runner is not None else subprocess.run
    completed = run(list(argv), check=False, shell=False)
    return int(completed.returncode)


def _require_installer_files(bind: HostBind, script: Path) -> None:
    if not bind.compose_file.is_file():
        raise FileNotFoundError(
            f"No docker-compose.yml under {bind.root}. Pass --root to the local-quality directory."
        )
    if not script.is_file():
        raise FileNotFoundError(
            f"No {script.name} under {bind.root}. Pass --root to the local-quality directory."
        )


def _windows_argv(
    script: Path,
    bind: HostBind,
    reset_volume: bool,
    skip_bootstrap: bool,
) -> list[str]:
    argv = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        "-Root",
        str(bind.root),
        "-SonarPort",
        str(bind.sonar_port),
        "-SonarMcpUrl",
        bind.sonar_mcp_url,
    ]
    if reset_volume:
        argv.append("-ResetVolume")
    if skip_bootstrap:
        argv.append("-SkipBootstrap")
    return argv


def _posix_argv(
    script: Path,
    bind: HostBind,
    reset_volume: bool,
    skip_bootstrap: bool,
) -> list[str]:
    argv = [
        str(script),
        "--root",
        str(bind.root),
        "--sonar-port",
        str(bind.sonar_port),
        "--sonar-mcp-url",
        bind.sonar_mcp_url,
    ]
    if reset_volume:
        argv.append("--reset")
    if skip_bootstrap:
        argv.append("--skip-bootstrap")
    return argv


def prepare_sonar_install(bind: HostBind) -> None:
    assert_local_sonar_url(bind.sonar_mcp_url)
