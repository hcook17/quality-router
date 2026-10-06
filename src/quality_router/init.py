"""qr init: stamp portable quality rule, hooks runner, and gitnexus off-marker.

Portable by default. Optional --host adapters (cursor, vscode, claude-code).
Optional --graph gortex constituent note. Idempotent. No tokens. No mcp.json.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from quality_router.harness.ci import stamp_ci
from quality_router.harness.policy import HOST_HOOK_STAMPS, stamp_policy

# --------------------------------------------------------------------------- #
# Portable stamp contents
# --------------------------------------------------------------------------- #

PORTABLE_RULE_MD = """\
# Quality Router Rule

This project uses quality-router for independent quality constituents.

## Constituents
- SonarQube (local only, 127.0.0.1 / host.docker.internal)
- Gortex (optional, CLI-only in this tree)
- Semgrep
- Spectral
- arXiv

## Hooks
Run quality checks before committing:
- POSIX: `.quality-router/hooks.sh`
- Windows: `.quality-router/hooks.ps1`

## GitNexus
GitNexus is disabled. Off markers:
- `.quality-router/gitnexus-hooks.off`
- `.cursor/gitnexus-hooks.off` (if --host cursor)

Do not set GITNEXUS_HOOKS=0.
"""

HOOKS_SH = """\
#!/usr/bin/env bash
# Quality-router hooks runner (POSIX)
# Run quality checks before committing.

set -e

echo "Running quality checks..."

if command -v semgrep &> /dev/null; then
    echo "Running semgrep..."
    semgrep --config auto . || true
fi

if command -v spectral &> /dev/null; then
    echo "Running spectral..."
    spectral lint . || true
fi

echo "Quality checks complete."
"""

HOOKS_PS1 = """\
# Quality-router hooks runner (Windows PowerShell)
# Run quality checks before committing.

Write-Host "Running quality checks..."

$ErrorActionPreference = "Continue"

if (Get-Command semgrep -ErrorAction SilentlyContinue) {
    Write-Host "Running semgrep..."
    semgrep --config auto . | Out-Null
}

if (Get-Command spectral -ErrorAction SilentlyContinue) {
    Write-Host "Running spectral..."
    spectral lint . | Out-Null
}

Write-Host "Quality checks complete."
"""

CURSOR_RULE_MDC = """\
---
name: quality-router
description: Independent quality constituents (Sonar, Gortex, Semgrep, Spectral, arXiv)
---

# Quality Router

This project uses quality-router for independent quality constituents.

## Constituents
- SonarQube (local only)
- Gortex (CLI-only in this tree)
- Semgrep
- Spectral
- arXiv

## Hooks
Run `.quality-router/hooks.ps1` (Windows) or `.quality-router/hooks.sh` (POSIX) before committing.

## GitNexus
Disabled. Do not set GITNEXUS_HOOKS=0.
"""

GORTEX_YAML_TEMPLATE = """\
# Gortex workspace (quality-router constituent)
workspace: {workspace}
{cross_deps}
"""

GORTEX_YAML_DEPS_HEADER = """\
  cross_workspace_deps:
"""

GORTEX_YAML_DEP_ITEM = """\
    - workspace: {dep_slug}
      module: {module_path}
"""


# --------------------------------------------------------------------------- #
# Host adapter strategies (OCP — adding a host does not fork cli.py)
# --------------------------------------------------------------------------- #

class HostAdapter:
    """Stamp a host-specific rule/hooks files. Idempotent."""

    def stamp(self, cwd: Path) -> None:
        raise NotImplementedError


class CursorAdapter(HostAdapter):
    def stamp(self, cwd: Path) -> None:
        cursor_dir = cwd / ".cursor"
        rules_dir = cursor_dir / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)

        rule_path = rules_dir / "quality-router.mdc"
        if not rule_path.exists():
            rule_path.write_text(CURSOR_RULE_MDC, encoding="utf-8")

        gitnexus_off = cursor_dir / "gitnexus-hooks.off"
        if not gitnexus_off.exists():
            gitnexus_off.write_text("", encoding="utf-8")


class VsCodeAdapter(HostAdapter):
    def stamp(self, cwd: Path) -> None:
        vscode_dir = cwd / ".vscode"
        vscode_dir.mkdir(exist_ok=True)

        instructions_path = vscode_dir / "quality-router-instructions.md"
        if not instructions_path.exists():
            instructions_path.write_text(PORTABLE_RULE_MD, encoding="utf-8")


class ClaudeCodeAdapter(HostAdapter):
    def stamp(self, cwd: Path) -> None:
        claude_md = cwd / "CLAUDE.md"
        if not claude_md.exists():
            claude_md.write_text(PORTABLE_RULE_MD, encoding="utf-8")


ADAPTERS: dict[str, HostAdapter] = {
    "cursor": CursorAdapter(),
    "vscode": VsCodeAdapter(),
    "claude-code": ClaudeCodeAdapter(),
}


# --------------------------------------------------------------------------- #
# Init configuration
# --------------------------------------------------------------------------- #

@dataclass
class InitConfig:
    cwd: Path
    host: str | None = None
    graph: str | None = None
    workspace: str | None = None
    workspace_deps: list[tuple[str, str]] = field(default_factory=list)
    no_gitnexus: bool = False
    policy: bool = False
    ci: str | None = None
    ci_java: int | None = None


# --------------------------------------------------------------------------- #
# Main init logic
# --------------------------------------------------------------------------- #

def run_init(config: InitConfig) -> None:
    """Stamp portable and optional host/graph stamps into cwd."""
    cwd = config.cwd

    # 1. Portable stamps (always)
    _write_portable_stamps(cwd)

    # 2. Host adapter stamps (optional)
    if config.host and config.host in ADAPTERS:
        ADAPTERS[config.host].stamp(cwd)

    # 3. Gortex graph stamps (optional, no-op if gortex not on PATH)
    if config.graph == "gortex":
        _write_gortex_config(cwd, config.workspace, config.workspace_deps)

    # 4. Agent policy + host hook wiring (optional)
    if config.policy:
        stamp_policy(cwd)
        if config.host in HOST_HOOK_STAMPS:
            HOST_HOOK_STAMPS[config.host](cwd)

    # 5. CI template (optional)
    if config.ci:
        stamp_ci(cwd, config.ci, config.ci_java)


def _write_portable_stamps(cwd: Path) -> None:
    """Write portable quality-router stamps. Idempotent."""
    qr_dir = cwd / ".quality-router"
    qr_dir.mkdir(exist_ok=True)

    # Generic agent rule
    rule_path = qr_dir / "rule.md"
    if not rule_path.exists():
        rule_path.write_text(PORTABLE_RULE_MD, encoding="utf-8")

    # POSIX hooks runner
    hooks_sh = qr_dir / "hooks.sh"
    if not hooks_sh.exists():
        hooks_sh.write_text(HOOKS_SH, encoding="utf-8")
        os.chmod(hooks_sh, 0o755)

    # Windows hooks runner
    hooks_ps1 = qr_dir / "hooks.ps1"
    if not hooks_ps1.exists():
        hooks_ps1.write_text(HOOKS_PS1, encoding="utf-8")

    # GitNexus off marker (portable)
    gitnexus_off = qr_dir / "gitnexus-hooks.off"
    if not gitnexus_off.exists():
        gitnexus_off.write_text("", encoding="utf-8")


def _write_gortex_config(cwd: Path, workspace: str | None, deps: list[tuple[str, str]]) -> None:
    """Write .gortex.yaml if gortex is on PATH. No-op if disconnected."""
    if not shutil.which("gortex"):
        return  # disconnected constituent → no-op

    slug = workspace or cwd.name
    gortex_yaml = cwd / ".gortex.yaml"

    if not gortex_yaml.exists():
        cross_deps_list = ""
        if deps:
            items = "\n".join(
                GORTEX_YAML_DEP_ITEM.format(dep_slug=s, module_path=m)
                for s, m in deps
            )
            cross_deps_list = GORTEX_YAML_DEPS_HEADER + items

        content = GORTEX_YAML_TEMPLATE.format(workspace=slug, cross_deps=cross_deps_list)
        gortex_yaml.write_text(content, encoding="utf-8")
