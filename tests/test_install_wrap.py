from pathlib import Path
from types import SimpleNamespace

import pytest

from quality_router.host_bind import HostBind, bind_host
from quality_router.install_wrap import build_installer_argv, invoke_installer, refuse_remote_pipe


def _bind(root: Path) -> HostBind:
    return bind_host(
        root_flag=str(root),
        sonar_port_flag=9000,
        sonar_mcp_url_flag="http://host.docker.internal:9000",
        environ={},
    )


def test_windows_argv_uses_file_not_irm(local_quality_root: Path) -> None:
    argv = build_installer_argv(
        _bind(local_quality_root),
        reset_volume=True,
        skip_bootstrap=True,
        windows=True,
    )
    assert argv[0] == "powershell"
    assert "-File" in argv
    assert str(local_quality_root / "install.ps1") in argv
    assert "-ResetVolume" in argv
    assert "-SkipBootstrap" in argv
    joined = " ".join(argv).lower()
    assert "irm |" not in joined
    assert "| iex" not in joined


def test_posix_argv_maps_installer_flags(local_quality_root: Path) -> None:
    argv = build_installer_argv(
        _bind(local_quality_root),
        reset_volume=True,
        skip_bootstrap=True,
        windows=False,
    )
    assert argv[0] == str(local_quality_root / "install.sh")
    assert argv[argv.index("--root") + 1] == str(local_quality_root.absolute())
    assert "--reset" in argv
    assert "--skip-bootstrap" in argv


def test_posix_argv_omits_optional_switches(local_quality_root: Path) -> None:
    argv = build_installer_argv(
        _bind(local_quality_root),
        reset_volume=False,
        skip_bootstrap=False,
        windows=False,
    )
    assert "--reset" not in argv
    assert "--skip-bootstrap" not in argv


def test_missing_compose_raises(tmp_path: Path) -> None:
    (tmp_path / "install.ps1").write_text("# x\n", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="docker-compose.yml"):
        build_installer_argv(
            _bind(tmp_path),
            reset_volume=False,
            skip_bootstrap=False,
            windows=True,
        )


def test_missing_script_raises(tmp_path: Path) -> None:
    (tmp_path / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="install.ps1"):
        build_installer_argv(
            _bind(tmp_path),
            reset_volume=False,
            skip_bootstrap=False,
            windows=True,
        )


def test_refuse_remote_pipe() -> None:
    with pytest.raises(ValueError, match=r"irm\|iex"):
        refuse_remote_pipe(["powershell", "-Command", "irm https://example.invalid | iex"])


def test_invoke_installer_uses_shell_false(local_quality_root: Path) -> None:
    argv = build_installer_argv(
        _bind(local_quality_root),
        reset_volume=False,
        skip_bootstrap=True,
        windows=True,
    )
    seen: dict[str, object] = {}

    def runner(command: list[str], *, check: bool, shell: bool) -> SimpleNamespace:
        seen["command"] = command
        seen["check"] = check
        seen["shell"] = shell
        return SimpleNamespace(returncode=0)

    assert invoke_installer(argv, runner=runner) == 0
    assert seen["shell"] is False
    assert seen["check"] is False
    assert seen["command"] == argv


@pytest.mark.parametrize(
    "argv",
    [
        ["powershell", "-Command", "Invoke-Expression Get-Process"],
        ["powershell", "-Command", "Invoke-RestMethod https://example.invalid"],
    ],
)
def test_refuse_invoke_cmdlets(argv: list[str]) -> None:
    with pytest.raises(ValueError, match=r"irm\|iex"):
        refuse_remote_pipe(argv)


def test_invoke_installer_default_runner_shell_false(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def fake_run(command: list[str], *, check: bool, shell: bool):
        seen["shell"] = shell
        seen["command"] = command
        return SimpleNamespace(returncode=4)

    monkeypatch.setattr("quality_router.install_wrap.subprocess.run", fake_run)
    assert invoke_installer(["powershell", "-File", "install.ps1"]) == 4
    assert seen["shell"] is False
