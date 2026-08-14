"""Resolve local-quality host paths: flags > env > defaults."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_SONAR_PORT = 9000
LOCAL_QUALITY_ROOT_ENV = "LOCAL_QUALITY_ROOT"
SONAR_PORT_ENV = "SONAR_PORT"
SONARQUBE_URL_ENV = "SONARQUBE_URL"
LOCAL_SONAR_HOSTS = frozenset(
    {"127.0.0.1", "localhost", "host.docker.internal", "::1"}
)


@dataclass(frozen=True)
class HostBind:
    root: Path
    sonar_port: int
    sonar_mcp_url: str

    @property
    def listen_url(self) -> str:
        return f"http://127.0.0.1:{self.sonar_port}"

    @property
    def compose_file(self) -> Path:
        return self.root / "docker-compose.yml"

    def installer_script(self, *, windows: bool) -> Path:
        name = "install.ps1" if windows else "install.sh"
        return self.root / name


def default_local_quality_root() -> Path:
    return Path.home() / "dev" / "local-quality"


def bind_host(
    *,
    root_flag: str | None,
    sonar_port_flag: int | None,
    sonar_mcp_url_flag: str | None,
    environ: dict[str, str] | None = None,
) -> HostBind:
    env = environ if environ is not None else dict(_os_environ())
    root = _first_nonempty(
        root_flag,
        env.get(LOCAL_QUALITY_ROOT_ENV),
        str(default_local_quality_root()),
    )
    port = _first_port(sonar_port_flag, env.get(SONAR_PORT_ENV), DEFAULT_SONAR_PORT)
    url = _first_nonempty(
        sonar_mcp_url_flag,
        env.get(SONARQUBE_URL_ENV),
        f"http://host.docker.internal:{port}",
    )
    return HostBind(root=_as_path(root), sonar_port=port, sonar_mcp_url=url)


def is_local_sonar_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.hostname or "").lower()
    return host in LOCAL_SONAR_HOSTS


def assert_local_sonar_url(url: str) -> None:
    if not is_local_sonar_url(url):
        raise ValueError("refusing non-local Sonar URL")


def _os_environ() -> dict[str, str]:
    import os

    return dict(os.environ)


def _as_path(raw: str) -> Path:
    return Path(raw).expanduser().absolute()


def _first_nonempty(*values: str | None) -> str:
    for value in values:
        if value:
            return value
    raise ValueError("missing host bind value")


def _first_port(flag: int | None, env_value: str | None, default: int) -> int:
    if flag is not None:
        return flag
    if env_value:
        return int(env_value)
    return default
