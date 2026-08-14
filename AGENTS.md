# quality-router (this tree)

Host-ops product. Merge SoT here is **uv.lock** + tests.

`qr` is **not locked to Cursor** (or any other agent host). Cursor is one optional stamp adapter.

## Invariants

- Independent constituents stay removable: Gortex, Semgrep, Spectral, local Sonar, arXiv.
- Disconnected constituent must no-op (portable marker `.quality-router/gitnexus-hooks.off`; Cursor trees may also use `.cursor/gitnexus-hooks.off`). Do not set `GITNEXUS_HOOKS=0`.
- Deterministic CLI decides enable/disable. The LLM proposes; `qr` verifies/commits/rejects (SDB).
- Do not add a visualization MCP. Do not wrap Context7+AlphaXiv+DeepWiki+Gortex in a Proxy Aggregator.
- Do not put a local LLM (Ollama/Hermes) between the **agent host** and MCP servers. Do not put `qr` on the LLM HTTP path either. Cheap-vs-expensive **model** pick is the host’s (or an opt-in BYOK gateway the host points at). RAG-MCP-style retrieval only if the live tool catalog exceeds ~10–15 tools.
- Tokens stay in the environment (`SONARQUBE_TOKEN`, `ALPHAXIV_API_KEY`, `CONTEXT7_API_KEY`, …) or `QUALITY_ROUTER_SECRETS` / `~/.config/quality-router/secrets`. Host secret dirs (e.g. `~/.cursor/secrets`) are adapters, not the product store. No secrets in any host’s `mcp.json`.
- Installers: flags > env > defaults. Do not `irm | iex`.
- Local Sonar only (`127.0.0.1` / `host.docker.internal`). Do not probe org/employer Sonar.

## Shared SoT (mixed hosts)

Employees may run Hermes, Claude Code, Codex, or Cursor. Two
mutating directors must not share **one working tree**. Parallel
work uses a clone or git worktree, then a PR.

Anything another host or machine must read is **committed**
(this file, `docs/research/architecture-decisions.md`, command
specs under `docs/design/phase-*.md`). `docs/local/` is
machine-local and gitignored — CONTINUE pastes do not travel.
A host that refreshes from the remote sees only pushed commits.
Handoff = commit + push, not the chat transcript.

## First work

1. `qr --help` / `qr status` skeleton.
2. Wrap `$LOCAL_QUALITY_ROOT` `install.ps1` (and `install.sh`); default root `~/dev/local-quality`.
3. `qr init` stamps a **portable** rule + hooks runner + `--no-gitnexus` marker. Optional `--host cursor|vscode|claude-code` adapters. Do not require Cursor.
4. Optional spike: Ollama daemon on `:11434` and `hermes` on PATH — diagnosis only, separate from the mediator.
