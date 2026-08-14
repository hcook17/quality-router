from pathlib import Path

import pytest

from quality_router.host_bind import (
    DEFAULT_SONAR_PORT,
    bind_host,
    default_local_quality_root,
    is_local_sonar_url,
)


def test_flag_beats_env_for_root(tmp_path: Path) -> None:
    env_root = tmp_path / "from-env"
    flag_root = tmp_path / "from-flag"
    bind = bind_host(
        root_flag=str(flag_root),
        sonar_port_flag=None,
        sonar_mcp_url_flag=None,
        environ={"LOCAL_QUALITY_ROOT": str(env_root), "SONAR_PORT": "9001"},
    )
    assert bind.root == flag_root.absolute()
    assert bind.sonar_port == 9001


def test_env_beats_defaults(tmp_path: Path) -> None:
    env_root = tmp_path / "from-env"
    bind = bind_host(
        root_flag=None,
        sonar_port_flag=None,
        sonar_mcp_url_flag=None,
        environ={
            "LOCAL_QUALITY_ROOT": str(env_root),
            "SONAR_PORT": "9111",
            "SONARQUBE_URL": "http://127.0.0.1:9111",
        },
    )
    assert bind.root == env_root.absolute()
    assert bind.sonar_port == 9111
    assert bind.sonar_mcp_url == "http://127.0.0.1:9111"


def test_defaults_when_nothing_set() -> None:
    bind = bind_host(
        root_flag=None,
        sonar_port_flag=None,
        sonar_mcp_url_flag=None,
        environ={},
    )
    assert bind.root == default_local_quality_root().absolute()
    assert bind.sonar_port == DEFAULT_SONAR_PORT
    assert bind.sonar_mcp_url == "http://host.docker.internal:9000"
    assert bind.listen_url == "http://127.0.0.1:9000"


def test_url_and_port_flags_beat_env(tmp_path: Path) -> None:
    bind = bind_host(
        root_flag=None,
        sonar_port_flag=9005,
        sonar_mcp_url_flag="http://127.0.0.1:9005",
        environ={
            "LOCAL_QUALITY_ROOT": str(tmp_path / "env"),
            "SONAR_PORT": "9001",
            "SONARQUBE_URL": "http://127.0.0.1:9001",
        },
    )
    assert bind.sonar_port == 9005
    assert bind.sonar_mcp_url == "http://127.0.0.1:9005"
    assert bind.root == (tmp_path / "env").absolute()


def test_flag_port_shapes_default_url() -> None:
    bind = bind_host(
        root_flag=None,
        sonar_port_flag=9002,
        sonar_mcp_url_flag=None,
        environ={},
    )
    assert bind.sonar_mcp_url == "http://host.docker.internal:9002"


def test_local_sonar_hosts() -> None:
    assert is_local_sonar_url("http://127.0.0.1:9000")
    assert is_local_sonar_url("http://localhost:9000")
    assert is_local_sonar_url("http://host.docker.internal:9000")
    assert not is_local_sonar_url("https://sonarqube.example.com/")


def test_local_sonar_ipv6_and_https() -> None:
    assert is_local_sonar_url("http://[::1]:9000")
    assert is_local_sonar_url("https://127.0.0.1:9000")
    assert not is_local_sonar_url("file:///etc/passwd")
    assert not is_local_sonar_url("http://127.0.0.1.attacker.example")


def test_bind_host_reads_os_environ(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "from-os"
    monkeypatch.setenv("LOCAL_QUALITY_ROOT", str(root))
    monkeypatch.setenv("SONAR_PORT", "9333")
    bind = bind_host(
        root_flag=None,
        sonar_port_flag=None,
        sonar_mcp_url_flag=None,
    )
    assert bind.root == root.absolute()
    assert bind.sonar_port == 9333


def test_first_nonempty_requires_a_value() -> None:
    from quality_router.host_bind import _first_nonempty

    with pytest.raises(ValueError, match="missing host bind value"):
        _first_nonempty(None, "", None)


def test_assert_local_sonar_url_does_not_echo_host() -> None:
    from quality_router.host_bind import assert_local_sonar_url

    with pytest.raises(ValueError, match="refusing non-local Sonar URL") as caught:
        assert_local_sonar_url("https://sonar.corp.example")
    assert "sonar.corp.example" not in str(caught.value)
