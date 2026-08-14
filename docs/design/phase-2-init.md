# Phase 2: `qr init` (spec gate)

**Status:** implemented under `src/` + `tests/`. Architecture lock:
`docs/research/architecture-decisions.md`. Phase 1 (`help` / `status` /
`install`) stays as-is.

## Goal

`qr init` stamps a **portable** quality rule, a hooks runner, and a
`--no-gitnexus` marker into *any* service checkout. It is **not
Cursor-specific**. Gortex remains a removable constituent.

Cursor / VS Code / Claude Code are **optional adapters** (`--host`), not
the product.

## Commands

| Command | Behavior |
| --- | --- |
| `qr init` | Portable stamps into `--cwd`: generic agent rule, hooks runner, `.quality-router/gitnexus-hooks.off`. |
| `qr init --host cursor` | Also stamp Cursor rule/hooks paths (`.cursor/…`) for trees that use that host. Repeatable with other `--host` values. |
| `qr init --host vscode` | Also stamp VS Code / Copilot instruction paths. |
| `qr init --host claude-code` | Also stamp `CLAUDE.md` (or that host’s equivalent). |
| `qr init --graph gortex` | Same stamps, plus a Gortex *constituent* note if `gortex` is on PATH; no-op if disconnected. May write `.gortex.yaml` workspace/project from flags (see below). |
| `qr init --graph gortex --workspace <slug>` | Join this checkout to a **declared** logical service. Same slug in each microservice repo that should share **contracts**. Default without the flag: directory basename (isolated). |
| `qr init --graph gortex --workspace-dep <slug> --module <path>` | Opt-in `cross_workspace_deps` (read-only): symbol stubs may resolve into `<slug>`; contracts still do not cross. Repeatable `--module`. Out of the first init cut if it blows cohesion — document then implement. |
| `qr init --no-gitnexus` | Write the portable marker (and host-adapter copies if those hosts were requested). Never set `GITNEXUS_HOOKS=0`. |

Default is portable-only. Do not imply `--host cursor`.

## Invariants (must hold)

- Flags > env > defaults (same bind as Phase 1 where relevant).
- Disconnected constituent → no-op (same string family as `status`).
- Do not write tokens. Never create or edit any host MCP catalog
  (Cursor `mcp.json`, VS Code `mcp.json`, `.mcp.json`, …), including a
  Gortex server block. Do not copy the user catalog into the project.
  “Omit Gortex from an otherwise written `mcp.json`” is still a write.
- Do not write hardcoded workspace paths (`CURSOR_WORKSPACE`, home
  directories, other checkouts). Gortex workspace slug is a flag, not a pin.
- Do not `gortex workspace set-all`. Untracked repos stay an explicit gap.
- Do not add a visualization MCP, GitNexus MCP, or Hermes picker.
- `--host` adapters stamp that host’s **rule and hooks files** only. They
  never write LLM HTTP opt-ins: `ANTHROPIC_BASE_URL`, Cursor Override
  OpenAI Base URL, Copilot BYOK / `github.copilot.chat.customOAIModels`,
  Zed `language_models.api_url`, or equivalent. They never run
  `ollama serve`, bind `:11434`, or run `hermes mcp serve` / `hermes acp`.
- Do not dual-host a second director (Hermes or Faraday **plus** the IDE
  agent) from `qr init`.
- `--graph gortex` is Job B (workspace slug / `.gortex.yaml`). It is not
  a model router and does not point the host at Ollama.
- Do not install Gortex/GitNexus skill packs or slash-command trees
  (`gortex init --skills`, GitNexus CLAUDE.md dumps).
- Do not delete user-global skills, commands, hooks, or Cursor plugins.
- GitNexus off-marker: write portable `.quality-router/gitnexus-hooks.off`.
  `--host cursor` also writes `.cursor/gitnexus-hooks.off` for hooks that
  only walk that path. Never set `GITNEXUS_HOOKS=0`.
- Local Sonar URLs only if init mentions Sonar at all (prefer leave
  Sonar to `qr install --sonar`).
- Idempotent: second `qr init` does not duplicate the rule block.
- Host adapters are OCP strategies. Adding a host does not fork `cli.py`.

## Out of scope

Ollama/Hermes diagnosis. Model cascade. Proxy Aggregator. `qr enable` /
`disable`. Implementing every IDE on earth in the first `init` cut —
start with portable + `--host cursor` as the first adapter because many
existing trees already use `.cursor/gitnexus-hooks.off`. Uninstalling
user-global skills, slash commands, or editor plugins. Operator
window/plugin disable is not a stamp. SP-1 may appear on `qr status` as
`local_llm_mcp_picker=refused` (or a later disconnected no-op). `qr init`
must not start `:11434`. Do not add Ollama/Hermes stamps in this cut.

## Verify

- Tests for portable marker, optional Cursor adapter, rule stamp, no
  `GITNEXUS_HOOKS` mutation, no mcp.json write. Init must not spawn
  Ollama/Hermes or write LLM base-URL / BYOK settings.
- `qr init` with no `--host` does not require a `.cursor/` directory.
- Coverage floor 98.7% on `quality_router`.
- `uv.lock` committed with any new deps (expect none).
