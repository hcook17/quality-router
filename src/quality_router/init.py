"""qr init: stamp portable quality rule, hooks runner, and gitnexus off-marker.

Portable by default. Optional --host adapters (cursor, vscode, claude-code).
Optional --graph gortex constituent note. Idempotent. No tokens. No mcp.json.
"""

from __future__ import annotations

import os
import re
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

GORTEX_YAML_HEADER = """\
# Written by `qr init --graph gortex`. qr never overwrites this file.
# Settings follow research/harness-kb/implementations.md (quality-router):
#   embedding off: embedding indexes are poisonable and localize Java poorly
#   facade-v1 in hide mode: about 15 inlined tools still select well
#   Java Kafka boundaries declared: Gortex does not detect them for Java
"""

GORTEX_YAML_BODY = """\
embedding:
  enabled: false
mcp:
  tools:
    preset: facade-v1
    mode: hide
index:
  event_bus:
    - name: kafka
      type: producer
      callee: kafkaTemplate.send
      topic_arg: "0"
    - name: kafka
      type: consumer
      decorator: KafkaListener
      topic_arg: topics
"""

GORTEX_NEXT_STEPS = """\
next: gortex install --hook-mode=enrich   # hooks add graph context, never deny Read/Grep
next: gortex init --no-skills             # no generated SKILL.md routing files
next: install jdtls so Gortex confirms Java edges over LSP
next: full reindex before trusting a cross-repo contract result in CI
"""

GORTEX_DISCONNECTED = (
    "gortex not on PATH; .gortex.yaml not written. Install a signed package "
    "(brew install zzet/tap/gortex, scoop, .deb/.rpm), then re-run."
)

GORTEX_OLDER_SHAPE = (
    "warning: .gortex.yaml was written by an older qr and Gortex rejects it "
    "(indented cross_workspace_deps / `module:`). Delete it and re-run qr init --graph gortex."
)

_SLUG = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_MODULE = re.compile(r"[A-Za-z0-9._/@:-]+")
_OLDER_SHAPE = re.compile(r"^(\s+cross_workspace_deps:|\s*-?\s*module:)", re.MULTILINE)


class InitError(ValueError):
    pass


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

def run_init(config: InitConfig) -> str | None:
    """Stamp portable and optional host/graph stamps into cwd; return the gortex status."""
    cwd = config.cwd
    gortex_status = None
    if config.graph == "gortex":
        validate_gortex(config)

    # 1. Portable stamps (always)
    _write_portable_stamps(cwd)

    # 2. Host adapter stamps (optional)
    if config.host and config.host in ADAPTERS:
        ADAPTERS[config.host].stamp(cwd)

    # 3. Gortex graph stamps (optional, no-op if gortex not on PATH)
    if config.graph == "gortex":
        gortex_status = _write_gortex_config(cwd, config.workspace, config.workspace_deps)

    # 4. Agent policy + host hook wiring (optional)
    if config.policy:
        stamp_policy(cwd)
        if config.host in HOST_HOOK_STAMPS:
            HOST_HOOK_STAMPS[config.host](cwd)

    # 5. CI template (optional)
    if config.ci:
        stamp_ci(cwd, config.ci, config.ci_java)
    return gortex_status


def validate_gortex(config: InitConfig) -> None:
    """Reject values that are not plain slugs/module names before anything is written."""
    if config.workspace is not None and not _SLUG.fullmatch(config.workspace):
        raise InitError(f"--workspace {config.workspace!r} is not a slug "
                        "(letters, digits, '.', '_', '-')")
    for dep, module in config.workspace_deps:
        if not _SLUG.fullmatch(dep):
            raise InitError(f"--workspace-dep {dep!r} is not a slug "
                            "(letters, digits, '.', '_', '-')")
        if not _MODULE.fullmatch(module):
            raise InitError(f"--module {module!r} has characters outside [A-Za-z0-9._/@:-]")
    slug = config.workspace or config.cwd.name
    if config.workspace is None and shutil.which("gortex") and not _SLUG.fullmatch(slug):
        raise InitError(f"directory name {slug!r} is not a slug; pass --workspace <slug>")
    if any(dep == slug for dep, _ in config.workspace_deps):
        raise InitError(f"--workspace-dep {slug!r} is this workspace")


def older_gortex_shape(cwd: Path) -> bool:
    path = cwd / ".gortex.yaml"
    return path.is_file() and bool(_OLDER_SHAPE.search(path.read_text(encoding="utf-8",
                                                                       errors="replace")))


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


def _write_gortex_config(cwd: Path, workspace: str | None,
                         deps: list[tuple[str, str]]) -> str:
    """Write .gortex.yaml if gortex is on PATH. Never overwrites; no-op if disconnected."""
    if not shutil.which("gortex"):
        return "disconnected"
    gortex_yaml = cwd / ".gortex.yaml"
    if gortex_yaml.exists():
        return "exists"
    modules: dict[str, list[str]] = {}
    for dep, module in deps:
        listed = modules.setdefault(dep, [])
        if module not in listed:
            listed.append(module)
    lines = [f"workspace: {_quoted(workspace or cwd.name)}"]
    if modules:
        lines.append("cross_workspace_deps:")
        for dep, listed in modules.items():
            lines.append(f"  - workspace: {_quoted(dep)}")
            lines.append("    modules:")
            lines.extend(f"      - {_quoted(m)}" for m in listed)
            lines.append("    mode: read-only")
    gortex_yaml.write_text(GORTEX_YAML_HEADER + "\n".join(lines) + "\n" + GORTEX_YAML_BODY,
                           encoding="utf-8")
    return "written"


def _quoted(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
