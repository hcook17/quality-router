"""Optional agent-host adapters. qr does not require any one IDE."""

from __future__ import annotations

from pathlib import Path

# Project-relative MCP catalogs. Absent paths are skipped, not errors.
PROJECT_MCP_CATALOGS = (
    Path(".quality-router") / "mcp.json",
    Path(".cursor") / "mcp.json",
    Path(".vscode") / "mcp.json",
    Path(".mcp.json"),
)

GITNEXUS_OFF_MARKERS = (
    Path(".quality-router") / "gitnexus-hooks.off",
    Path(".cursor") / "gitnexus-hooks.off",
)

SONARQUBE_TOKEN_ENV = "SONARQUBE_TOKEN"
QUALITY_ROUTER_SECRETS_ENV = "QUALITY_ROUTER_SECRETS"


def product_secrets_dir(environ: dict[str, str] | None = None) -> Path:
    env = environ if environ is not None else {}
    flagged = env.get(QUALITY_ROUTER_SECRETS_ENV)
    if flagged:
        return Path(flagged).expanduser()
    return Path.home() / ".config" / "quality-router" / "secrets"


def cursor_secrets_dir() -> Path:
    return Path.home() / ".cursor" / "secrets"
