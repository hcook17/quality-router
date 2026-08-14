# quality-router

CLI mediator (`qr`) for independent quality constituents: local Sonar CE, Gortex, git hooks, Spectral, Semgrep, arXiv. Constituents stay removable. A disconnected constituent must no-op.

This is **not** an MCP aggregator. This is **not** a local-LLM host in front of those servers. This is **not** locked to Cursor (or any other agent host). Cursor is an optional `--host` stamp adapter.

`qr` is Job B (stamps, install, status, later enable/disable). Cheap vs expensive **model** pick is Job A inside the agent host you already run. The product reports `agent_host_lock=none`.

## Install

```text
uv tool install quality-router
qr --help
qr install --sonar --hooks --no-gitnexus
qr status
cd any-service
qr init --graph gortex
```

Phase 1 implements `--help`, `status`, and `install` (wraps `$LOCAL_QUALITY_ROOT` `install.ps1` / `install.sh`). Phase 2 `qr init` is spec-gated in `docs/design/phase-2-init.md` (not implemented yet). Do not `irm | iex`. Flags > env > defaults. Default init is portable; do not imply `--host cursor`.

## Layout

| Path | Role |
|------|------|
| `src/quality_router/` | CLI (`qr` / `quality-router`) |
| `AGENTS.md` | Invariants for agents in this tree |
| `docs/design/phase-1-cli.md` | Spec SoT for Phase 1 |
| `docs/design/phase-2-init.md` | Spec SoT for `qr init` |
| `docs/research/architecture-decisions.md` | C4 + three-job lock |

Ollama is an optional model backend a host may **opt** at (`:11434`). Hermes (or any other agent runtime) may be the director on your machine; `qr` does not start the Ollama daemon, write LLM base URLs, or `hermes mcp serve`. Neither sits between the host and constituent MCPs.
