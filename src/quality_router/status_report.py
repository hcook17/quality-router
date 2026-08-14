"""Host and constituent status. Local Sonar listen probe only."""

from __future__ import annotations

import json
import shutil
import socket
from collections.abc import Callable, Mapping
from pathlib import Path

from quality_router import __version__
from quality_router.agent_hosts import (
    GITNEXUS_OFF_MARKERS,
    PROJECT_MCP_CATALOGS,
    SONARQUBE_TOKEN_ENV,
    cursor_secrets_dir,
    product_secrets_dir,
)
from quality_router.constituents import disconnected_noop
from quality_router.host_bind import HostBind, is_local_sonar_url

WhichBinary = Callable[[str], str | None]
ListenProbe = Callable[[int], str]

_MCP_STATE_RANK = ("forbidden", "unreadable", "ok", "absent")


def report_status(
    bind: HostBind,
    *,
    cwd: Path,
    windows: bool,
    environ: Mapping[str, str],
    which: WhichBinary | None = None,
    listen: ListenProbe | None = None,
) -> str:
    which_fn = which if which is not None else shutil.which
    listen_fn = listen if listen is not None else probe_local_listen
    rows = [
        *host_rows(bind, windows=windows),
        *secret_rows(environ),
        *gitnexus_rows(cwd, environ),
        ("mcp_json_tokens", combined_mcp_token_state(cwd)),
        ("listen", listen_fn(bind.sonar_port)),
        *constituent_rows(bind, which_fn, windows=windows),
        ("visualization_mcp", "refused"),
        ("local_llm_mcp_picker", "refused"),
        ("agent_host_lock", "none"),
    ]
    return format_rows(rows)


def format_rows(rows: list[tuple[str, str]]) -> str:
    return "".join(f"{key}={value}\n" for key, value in rows)


def probe_local_listen(port: int) -> str:
    try:
        with socket.create_connection(("127.0.0.1", port), 0.2):
            return "up"
    except OSError:
        return "down"


def host_rows(bind: HostBind, *, windows: bool) -> list[tuple[str, str]]:
    script = bind.installer_script(windows=windows)
    local = is_local_sonar_url(bind.sonar_mcp_url)
    url_display = bind.sonar_mcp_url if local else "redacted_non_local"
    return [
        ("quality_router", __version__),
        ("agent_host_lock", "none"),
        ("local_quality_root", str(bind.root)),
        ("installer_script", str(script)),
        ("installer", _present(script.is_file())),
        ("compose", _present(bind.compose_file.is_file())),
        ("sonar_port", str(bind.sonar_port)),
        ("sonar_mcp_url", url_display),
        ("listen_url", bind.listen_url),
        ("sonar_mcp_local", "yes" if local else "no"),
    ]


def secret_rows(environ: Mapping[str, str]) -> list[tuple[str, str]]:
    product = product_secrets_dir(dict(environ))
    cursor = cursor_secrets_dir()
    env_token = "present" if environ.get(SONARQUBE_TOKEN_ENV) else "absent"
    return [
        ("sonar_token_env", env_token),
        ("secrets_dir", _present(product.is_dir())),
        ("host.cursor.secrets", _present(cursor.is_dir())),
        ("host.cursor.sonar_token_file", _present((cursor / "sonarqube-local-token").is_file())),
    ]


def gitnexus_rows(cwd: Path, environ: Mapping[str, str]) -> list[tuple[str, str]]:
    env_value = environ.get("GITNEXUS_HOOKS")
    env_report = "unset" if env_value is None else env_value
    posture = "ok"
    if env_value == "0":
        posture = "prefer_gitnexus-hooks.off_marker"
    return [
        ("gitnexus_hooks_env", env_report),
        ("gitnexus_off_marker", _present(_gitnexus_marker_present(cwd))),
        ("gitnexus_posture", posture),
    ]


def constituent_rows(
    bind: HostBind,
    which: WhichBinary,
    *,
    windows: bool,
) -> list[tuple[str, str]]:
    return [
        ("constituent.sonar", sonar_state(bind)),
        ("constituent.gortex", binary_state(which, "gortex")),
        ("constituent.semgrep", semgrep_state(which, windows=windows)),
        ("constituent.spectral", binary_state(which, "spectral")),
        ("constituent.arxiv", disconnected_noop("not stamped by qr")),
    ]


def sonar_state(bind: HostBind) -> str:
    if not is_local_sonar_url(bind.sonar_mcp_url):
        return disconnected_noop("refusing non-local Sonar URL")
    if not bind.compose_file.is_file():
        return disconnected_noop("compose missing")
    return "present"


def binary_state(which: WhichBinary, name: str) -> str:
    path = which(name)
    if path:
        return f"present ({path})"
    return disconnected_noop("binary not on PATH")


def semgrep_state(which: WhichBinary, *, windows: bool) -> str:
    path = which("semgrep")
    if not path:
        return disconnected_noop("binary not on PATH")
    if windows:
        return f"present ({path}); Windows extension experimental"
    return f"present ({path})"


def combined_mcp_token_state(cwd: Path) -> str:
    states = [mcp_json_token_state(cwd / rel) for rel in PROJECT_MCP_CATALOGS]
    for rank in _MCP_STATE_RANK:
        if rank in states:
            return rank
    return "absent"


def mcp_json_token_state(path: Path) -> str:
    if not path.is_file():
        return "absent"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return "unreadable"
    if any(_is_raw_secret(item) for item in _walk_strings(data)):
        return "forbidden"
    return "ok"


def _gitnexus_marker_present(cwd: Path) -> bool:
    return any((cwd / rel).is_file() for rel in GITNEXUS_OFF_MARKERS)


def _present(exists: bool) -> str:
    return "present" if exists else "absent"


def _walk_strings(node: object) -> list[str]:
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        found: list[str] = []
        for item in node.values():
            found.extend(_walk_strings(item))
        return found
    if isinstance(node, list):
        found = []
        for item in node:
            found.extend(_walk_strings(item))
        return found
    return []


def _is_raw_secret(value: str) -> bool:
    stripped = value.strip()
    if "${env:" in stripped:
        return False
    token = stripped.removeprefix("Bearer ").strip()
    return token.startswith(("squ_", "sk-", "ghp_", "glpat-"))
