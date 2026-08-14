import os
from pathlib import Path

import pytest

from quality_router.cli import run


def test_help_lists_status_and_install(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exited:
        run(["--help"])
    assert exited.value.code == 0
    out = capsys.readouterr().out
    assert "status" in out
    assert "install" in out
    assert "irm" in out
    assert "MCP aggregator" in out
    assert "agent host" in out


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exited:
        run(["--version"])
    assert exited.value.code == 0
    assert "quality-router 0.1.0" in capsys.readouterr().out


def test_status_uses_root_flag(
    local_quality_root: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(local_quality_root)
    assert run(["status", "--root", str(local_quality_root)]) == 0
    out = capsys.readouterr().out
    assert f"local_quality_root={local_quality_root}" in out
    assert "listen_url=http://127.0.0.1:9000" in out


def test_install_requires_constituent_flag(capsys: pytest.CaptureFixture[str]) -> None:
    assert run(["install"]) == 2
    assert "select at least one" in capsys.readouterr().err


def test_install_dry_run_sonar(
    local_quality_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = run(
        [
            "install",
            "--sonar",
            "--dry-run",
            "--skip-bootstrap",
            "--root",
            str(local_quality_root),
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "dry_run=" in out
    assert "irm |" not in out.lower()
    assert "| iex" not in out.lower()


def test_install_refuses_org_sonar(
    local_quality_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = run(
        [
            "install",
            "--sonar",
            "--dry-run",
            "--root",
            str(local_quality_root),
            "--sonar-mcp-url",
            "https://sonarqube.example.com/",
        ]
    )
    assert code == 1
    assert "refusing non-local Sonar URL" in capsys.readouterr().err


def test_no_gitnexus_does_not_set_env(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("GITNEXUS_HOOKS", raising=False)
    assert run(["install", "--no-gitnexus", "--hooks"]) == 0
    out = capsys.readouterr().out
    assert "hooks=deferred_to_qr_init" in out
    assert "gitnexus_off_marker=deferred_to_qr_init" in out
    assert "GITNEXUS_HOOKS" not in os.environ


def test_no_command_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert run([]) == 2
    assert "status" in capsys.readouterr().err


def test_install_missing_compose(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    code = run(["install", "--sonar", "--root", str(empty)])
    assert code == 1
    assert "docker-compose.yml" in capsys.readouterr().err


def test_install_missing_script(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "lq"
    root.mkdir()
    (root / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    code = run(["install", "--sonar", "--root", str(root)])
    assert code == 1
    err = capsys.readouterr().err
    assert "install.ps1" in err or "install.sh" in err


def test_install_invokes_wrapper(
    local_quality_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    def fake_invoke(argv: list[str]) -> int:
        seen["argv"] = list(argv)
        return 0

    monkeypatch.setattr("quality_router.cli.invoke_installer", fake_invoke)
    code = run(
        ["install", "--sonar", "--root", str(local_quality_root), "--skip-bootstrap"]
    )
    assert code == 0
    argv = seen["argv"]
    assert isinstance(argv, list)
    assert "-File" in argv or str(local_quality_root / "install.sh") in argv


def test_install_reset_volume_dry_run(
    local_quality_root: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = run(
        [
            "install",
            "--sonar",
            "--dry-run",
            "--reset-volume",
            "--root",
            str(local_quality_root),
        ]
    )
    assert code == 0
    out = capsys.readouterr().out.lower()
    assert "reset" in out


def test_entrypoint_and_package_main(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("quality_router.cli.run", lambda argv=None: 0)
    from quality_router.cli import entrypoint

    with pytest.raises(SystemExit) as exited:
        entrypoint()
    assert exited.value.code == 0

    called: list[bool] = []

    def fake_entrypoint() -> None:
        called.append(True)
        raise SystemExit(0)

    monkeypatch.setattr("quality_router.cli.entrypoint", fake_entrypoint)
    from quality_router import main as package_main

    with pytest.raises(SystemExit) as exited:
        package_main()
    assert called == [True]
    assert exited.value.code == 0


def test_run_none_uses_sys_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["qr", "install"])
    assert run(None) == 2
