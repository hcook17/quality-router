import json
from pathlib import Path

import pytest

from quality_router.host_bind import HostBind, bind_host
from quality_router.status_report import report_status


def _bind(root: Path, url: str = "http://host.docker.internal:9000") -> HostBind:
    return bind_host(
        root_flag=str(root),
        sonar_port_flag=9000,
        sonar_mcp_url_flag=url,
        environ={},
    )


def test_status_reports_disconnected_constituents(local_quality_root: Path, tmp_path: Path) -> None:
    cwd = tmp_path / "workspace"
    cwd.mkdir()
    text = report_status(
        _bind(local_quality_root),
        cwd=cwd,
        windows=True,
        environ={},
        which=lambda _name: None,
        listen=lambda _port: "down",
    )
    assert "constituent.sonar=present" in text
    assert "constituent.gortex=disconnected (no-op): binary not on PATH" in text
    assert "constituent.semgrep=disconnected (no-op): binary not on PATH" in text
    assert "constituent.spectral=disconnected (no-op): binary not on PATH" in text
    assert "constituent.arxiv=disconnected (no-op): not stamped by qr" in text
    assert "listen_url=http://127.0.0.1:9000" in text
    assert "listen=down" in text
    assert "gitnexus_hooks_env=unset" in text
    assert "mcp_json_tokens=absent" in text
    assert "agent_host_lock=none" in text


def test_semgrep_windows_notes_experimental(local_quality_root: Path, tmp_path: Path) -> None:
    text = report_status(
        _bind(local_quality_root),
        cwd=tmp_path,
        windows=True,
        environ={},
        which=lambda name: r"C:\semgrep\semgrep.exe" if name == "semgrep" else None,
        listen=lambda _port: "down",
    )
    assert "Windows extension experimental" in text


def test_gitnexus_env_zero_is_not_the_posture(local_quality_root: Path, tmp_path: Path) -> None:
    text = report_status(
        _bind(local_quality_root),
        cwd=tmp_path,
        windows=True,
        environ={"GITNEXUS_HOOKS": "0"},
        which=lambda _name: None,
        listen=lambda _port: "down",
    )
    assert "gitnexus_hooks_env=0" in text
    assert "prefer_gitnexus-hooks.off_marker" in text


def test_mcp_json_raw_token_is_forbidden(local_quality_root: Path, tmp_path: Path) -> None:
    mcp = tmp_path / ".cursor"
    mcp.mkdir()
    (mcp / "mcp.json").write_text(
        json.dumps(
            {"mcpServers": {"sonarqube": {"env": {"SONARQUBE_TOKEN": "squ_secret"}}}},
            indent=2,
        ),
        encoding="utf-8",
    )
    text = report_status(
        _bind(local_quality_root),
        cwd=tmp_path,
        windows=True,
        environ={},
        which=lambda _name: None,
        listen=lambda _port: "down",
    )
    assert "mcp_json_tokens=forbidden" in text
    assert "squ_secret" not in text


def test_mcp_json_env_interpolation_is_ok(local_quality_root: Path, tmp_path: Path) -> None:
    mcp = tmp_path / ".cursor"
    mcp.mkdir()
    (mcp / "mcp.json").write_text(
        json.dumps({"env": {"SONARQUBE_TOKEN": "${env:SONARQUBE_TOKEN}"}}),
        encoding="utf-8",
    )
    text = report_status(
        _bind(local_quality_root),
        cwd=tmp_path,
        windows=True,
        environ={},
        which=lambda _name: None,
        listen=lambda _port: "down",
    )
    assert "mcp_json_tokens=ok" in text


def test_mcp_json_unreadable_and_list_secret(local_quality_root: Path, tmp_path: Path) -> None:
    mcp = tmp_path / ".cursor"
    mcp.mkdir()
    (mcp / "mcp.json").write_text("{", encoding="utf-8")
    text = report_status(
        _bind(local_quality_root),
        cwd=tmp_path,
        windows=True,
        environ={},
        which=lambda _name: None,
        listen=lambda _port: "down",
    )
    assert "mcp_json_tokens=unreadable" in text

    other = tmp_path / "listed"
    cursor = other / ".cursor"
    cursor.mkdir(parents=True)
    (cursor / "mcp.json").write_text(json.dumps({"tokens": ["squ_nested"]}), encoding="utf-8")
    listed = report_status(
        _bind(local_quality_root),
        cwd=other,
        windows=False,
        environ={},
        which=lambda name: "/usr/bin/gortex" if name == "gortex" else None,
        listen=lambda _port: "down",
    )
    assert "mcp_json_tokens=forbidden" in listed
    assert "squ_nested" not in listed
    assert "constituent.gortex=present (/usr/bin/gortex)" in listed
    assert "constituent.semgrep=disconnected" in listed


def test_spectral_present(local_quality_root: Path, tmp_path: Path) -> None:
    text = report_status(
        _bind(local_quality_root),
        cwd=tmp_path,
        windows=False,
        environ={},
        which=lambda name: "/usr/bin/spectral" if name == "spectral" else None,
        listen=lambda _port: "down",
    )
    assert "constituent.spectral=present (/usr/bin/spectral)" in text


def test_semgrep_posix_present(local_quality_root: Path, tmp_path: Path) -> None:
    text = report_status(
        _bind(local_quality_root),
        cwd=tmp_path,
        windows=False,
        environ={},
        which=lambda name: "/usr/bin/semgrep" if name == "semgrep" else None,
        listen=lambda _port: "down",
    )
    assert "constituent.semgrep=present (/usr/bin/semgrep)" in text
    assert "experimental" not in text


def test_sonar_compose_missing_and_gitnexus_marker(tmp_path: Path) -> None:
    marker_dir = tmp_path / ".cursor"
    marker_dir.mkdir()
    (marker_dir / "gitnexus-hooks.off").write_text("", encoding="utf-8")
    text = report_status(
        _bind(tmp_path),
        cwd=tmp_path,
        windows=True,
        environ={},
        which=lambda _name: None,
        listen=lambda _port: "down",
    )
    assert "compose missing" in text
    assert "gitnexus_off_marker=present" in text
    assert "visualization_mcp=refused" in text
    assert "local_llm_mcp_picker=refused" in text


def test_status_defaults_and_bearer_secret(local_quality_root: Path, tmp_path: Path) -> None:
    text = report_status(
        _bind(local_quality_root),
        cwd=tmp_path,
        windows=True,
        environ={},
    )
    assert "constituent.sonar=present" in text
    assert "listen=" in text

    mcp = tmp_path / ".cursor"
    mcp.mkdir()
    (mcp / "mcp.json").write_text(
        json.dumps({"auth": "Bearer squ_from_header", "n": 1}),
        encoding="utf-8",
    )
    bearer = report_status(
        _bind(local_quality_root),
        cwd=tmp_path,
        windows=True,
        environ={},
        which=lambda _name: None,
        listen=lambda _port: "down",
    )
    assert "squ_from_header" not in bearer


def test_probe_local_listen_up_and_down() -> None:
    import socket

    from quality_router.status_report import probe_local_listen

    assert probe_local_listen(1) == "down"
    server = socket.create_server(("127.0.0.1", 0))
    port = int(server.getsockname()[1])
    try:
        assert probe_local_listen(port) == "up"
    finally:
        server.close()


def test_vscode_mcp_json_raw_token_is_forbidden(
    local_quality_root: Path, tmp_path: Path
) -> None:
    vscode = tmp_path / ".vscode"
    vscode.mkdir()
    (vscode / "mcp.json").write_text(
        json.dumps({"env": {"SONARQUBE_TOKEN": "squ_vscode"}}),
        encoding="utf-8",
    )
    text = report_status(
        _bind(local_quality_root),
        cwd=tmp_path,
        windows=True,
        environ={},
        which=lambda _name: None,
        listen=lambda _port: "down",
    )
    assert "mcp_json_tokens=forbidden" in text
    assert "squ_vscode" not in text


def test_portable_gitnexus_marker_without_cursor(tmp_path: Path) -> None:
    portable = tmp_path / ".quality-router"
    portable.mkdir()
    (portable / "gitnexus-hooks.off").write_text("", encoding="utf-8")
    text = report_status(
        _bind(tmp_path),
        cwd=tmp_path,
        windows=True,
        environ={},
        which=lambda _name: None,
        listen=lambda _port: "down",
    )
    assert "gitnexus_off_marker=present" in text


def test_sonar_token_env_is_reported(local_quality_root: Path, tmp_path: Path) -> None:
    text = report_status(
        _bind(local_quality_root),
        cwd=tmp_path,
        windows=True,
        environ={"SONARQUBE_TOKEN": "from-env"},
        which=lambda _name: None,
        listen=lambda _port: "down",
    )
    assert "sonar_token_env=present" in text
    assert "from-env" not in text


def test_empty_mcp_catalog_list_reports_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from quality_router import status_report

    monkeypatch.setattr(status_report, "PROJECT_MCP_CATALOGS", ())
    assert status_report.combined_mcp_token_state(tmp_path) == "absent"


def test_root_mcp_json_raw_token_is_forbidden(
    local_quality_root: Path, tmp_path: Path
) -> None:
    (tmp_path / ".mcp.json").write_text(
        json.dumps({"env": {"SONARQUBE_TOKEN": "squ_root"}}),
        encoding="utf-8",
    )
    text = report_status(
        _bind(local_quality_root),
        cwd=tmp_path,
        windows=True,
        environ={},
        which=lambda _name: None,
        listen=lambda _port: "down",
    )
    assert "mcp_json_tokens=forbidden" in text
    assert "squ_root" not in text


def test_product_secrets_dir_from_env(local_quality_root: Path, tmp_path: Path) -> None:
    secrets = tmp_path / "qr-secrets"
    secrets.mkdir()
    text = report_status(
        _bind(local_quality_root),
        cwd=tmp_path,
        windows=True,
        environ={"QUALITY_ROUTER_SECRETS": str(secrets)},
        which=lambda _name: None,
        listen=lambda _port: "down",
    )
    assert "secrets_dir=present" in text


def test_non_local_sonar_is_disconnected(local_quality_root: Path, tmp_path: Path) -> None:
    text = report_status(
        _bind(local_quality_root, url="https://sonarqube.example.com/"),
        cwd=tmp_path,
        windows=True,
        environ={},
        which=lambda _name: None,
        listen=lambda _port: "down",
    )
    assert "sonar_mcp_local=no" in text
    assert "refusing non-local Sonar URL" in text
    assert "sonarqube.example.com" not in text
    assert "sonar_mcp_url=redacted_non_local" in text
