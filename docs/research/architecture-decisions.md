# Architecture lock

This is the only architecture/research lock. Edit this file; do not add
sibling memos, epics, or “spec gates” for the same decisions.

Command specs (what to implement): `docs/design/phase-1-cli.md`,
`docs/design/phase-2-init.md`. Operator notes stay gitignored in
`docs/local/`. Merge SoT: **`uv.lock` + tests** (coverage ≥98.7% on
`quality_router`).

## What `qr` is

Host-ops stamp/verify CLI. Not an MCP aggregator, not a model router,
not locked to Cursor. The user already has an agent host; that host
talks **directly** to constituent MCPs. `qr` verifies, installs, stamps.

Optional `--host …` at `qr init` may write that host’s rule/hook files.
Portable stamps (rule text, git hooks, `.quality-router/gitnexus-hooks.off`)
work without an adapter.

## Three jobs (do not fuse)

| Job | Owner | Not |
| --- | --- | --- |
| A. Cheap vs expensive **model** | The agent host (or a later sibling host with written Z + held-out G_learn) | A cascade in front of MCP; `qr` MITM of prompts; Ollama as a silent interceptor |
| B. Which **MCP / tool** fires | Deterministic `qr` + rules + scoped listing | Local LLM as Proxy Aggregator |
| C. Two mutating **directors** on one working tree | Refuse | Hermes **plus** Cursor writing the same dirty tree |

Job C is “do not dual-write one working tree,” not “pick one host brand.”
N employees × N clones × mixed hosts sharing `origin` is allowed.
Parallel sessions use git worktrees, then a PR.

Ollama is an inference backend a host may **opt** at via base URL.
Hermes is another host (ACP) or extra MCP tools — not a MITM of another
host’s paid model. Tool/MCP audit logs belong on the **director host**
(local JSONL), not as a `qr` proxy.

## C4 (skip Code)

- **C1:** You use `quality-router` and *an* agent host. `qr` wraps
  `~/dev/local-quality` and stamps portable (plus optional host) config.
  No edge Agent → Ollama → Gortex.
- **C2:** `qr` CLI (verifier), optional host adapters (stamps), graph-3d
  HTML (presentation, not an MCP). Host router = job A.
- **C3:** `install` / `init` / `status` / SDB gate (catalog cliff ~10–15
  tools; no Gortex+GitNexus+Serena).

## Language and CLI contract

- **Python 3.13** + stdlib **`argparse`**. No Typer, Click, Cyclopts,
  Cobra, clap, Fang, Rich prompts, or TUI as the agent surface.
- Do not rewrite in Go/Rust because Gortex is Go. Papers pick a CLI
  *contract*, not a language.
- Every command: non-interactive flags, layered `--help` with Examples,
  `--dry-run` on mutating commands, argv lists (`shell=False`), Windows
  installer via `powershell -File` never `-Command`.
- Optional `--json` on report commands **after** `qr init`, additive,
  no new deps.
- Shipping a single `qr.exe` for machines without Python is a later
  **distribution** epic (Go+Cobra *or* uv-packaged Python). Not this tip.
- Do not replace `local-quality` `install.ps1` from this tree.

## WASM, tokens, intercept

WASM’s unique job is sandboxing untrusted composition code on a **Job A
runtime**. It is not this stamp CLI.

- **Refuse** in-process Wasmtime / Extism / component model / PyO3 in
  this tree. Deterministic gates stay Python predicates
  ([2607.07405](https://arxiv.org/abs/2607.07405)).
- **Refuse** WASM as a token filter. Token win is what the model sees:
  CLI vs MCP catalog, `--json`, CodeAct on the **host** — not bytecode.
- **Refuse** `qr` intercepting agent shell scripts. MITM of the host’s
  shell is Job A leakage. WASI that cannot spawn `uv` / docker /
  `powershell -File` cannot run this product; WASI that can is a second
  shell.
- A plugin VM is delayed until untrusted third-party adapters exist.

## Multi-host SoT

- **Team SoT** is git: committed `AGENTS.md`, this file, command specs,
  `uv.lock`, tests.
- **Machine-local** stays gitignored: `docs/local/`, `.worktrees/`, host
  secret dirs.
- Handoff to another host or machine = **commit + push**. Uncommitted
  files and `docs/local/` are invisible to cloud/remote clones.
- `AGENTS.md` is canonical. Optional `--host claude-code` may stamp a
  one-line `CLAUDE.md` that imports `@AGENTS.md`. Do not maintain three
  divergent instruction files.
- `qr` does not watch files, merge worktrees, or proxy transcripts
  between Hermes, Claude, Codex, and Cursor.
- Context7 (and every billed MCP): API key in **every** host’s
  environment / secrets adapter. No secrets in `mcp.json`. Do not add a
  Context7 cache/gateway as `qr` (that is a Proxy Aggregator).

## RL / on-policy distillation

`qr` is a **verifiable CLI** a gym *may wrap* (exit codes, later
`--json`). It is not the gym, the snapshot kernel, or the student.

SEED / BPO / TurnOPD / DiDPO train **Job A** in Docker/test sandboxes
on a **sibling host** (same bucket as Faraday / FairTutor): written
signal Z and held-out G_learn required. Not a `qr` subcommand.

WASM/WASI is not the SWE sandbox. Snapshot/restore is
Docker/overlayfs-class. Do not put a distilled local model between any
agent host and MCP. Do not distill Cursor or Hermes transcripts into
Ollama weights in this tree.

## Sibling hosts (not this repo)

A 27B director that calls a frontier coding agent as a tool is Faraday
[2608.13331](https://arxiv.org/abs/2608.13331). A 7B orchestrator with
executor cost profiles is EASY [2608.04588](https://arxiv.org/abs/2608.04588).
A cheap-first tutoring cascade with evaluator threshold τ is FairTutor
[2606.20713](https://arxiv.org/abs/2606.20713). SWE papers invert the
split: small explorer, frontier still solves (FastContext
[2606.14066](https://arxiv.org/abs/2606.14066), CodeGrep
[2608.05886](https://arxiv.org/abs/2608.05886), SWE-Pruner Pro
[2607.18213](https://arxiv.org/abs/2607.18213)). Pre-answer routers
recover 7.5–14.4% of a certified 9.7–30.7 pp oracle gap
([2608.08265](https://arxiv.org/abs/2608.08265)). MCP expose-all still
fails (SkillWeaver [2606.18051](https://arxiv.org/abs/2606.18051);
Haiku cliff 10–15 tools, Rodrigues & Vas
[2606.30317](https://arxiv.org/abs/2606.30317)). A cloud gateway that
breaks direct-connect ([2607.15593](https://arxiv.org/abs/2607.15593))
is refused here.

An MCP `ask` cascade (`escalation-gate`) is that later Job A sibling,
not a `qr` subcommand and not a phase in this tree. It does not route
director completions. Honest pitch: gated answers for questions the
host chooses to send. If that sibling is built, these pre-Phase-1
locks apply (2026-08-15):

1. Sibling repo only. Do not open a `docs/design/phase-N` here for it.
2. One OpenAI-compat client. Probe for logprobs at runtime; fall back
   to `ChatOllama` only on probe failure. Do not lock “Ollama `/v1`
   supports logprobs” or “does not.” Public evidence conflicts
   (v0.12.11 release-note headline vs current docs checkbox vs
   ollama/ollama#16117 closed as not planned). Do not write
   “#16117 proves `/v1` works” into any lock.
3. Generate once. Either UQLM owns local generate+score, or the
   orchestrator generates samples and calls `score()` only.
4. Cascade-vs-router bake-off on a synthetic set **before** Phase 1.
   If the router wins, stop.
5. If a cascade still wins, prefer white-box (or vLLM) in production.
   Black-box is a portability fallback, not the default. Do not
   default to N+1 local generations. `noncontradiction` NLI is an
   explicit dep if used.
6. No `explain_last()`. Trace rides on `ask`, or a client-held request id.
7. Fail-closed matrix and a single calibrator SoT (artifact owns tau;
   config does not silently override) before any FastMCP stub.

UCCI’s cost-optimality does not transfer from token-margin to
black-box consistency. Zellinger & Thomson’s 4.3% error-cost AUC
gain is for k≥3 and does not back a k=2 design. Coverage floor in
*this* tree remains 98.7%. Model cascade stays out of scope for
`qr init` / this product.

## Build sequence

1. Phase 1 CLI — **done** (`help` / `status` / `install`).
2. Phase 2 `qr init` — **done** (portable stamps, `--host` adapters,
   `--graph gortex`). Spec: `docs/design/phase-2-init.md`.
3. Next: `--json` on report commands, then `enable` / `disable`.

Do not reopen Go, Wasmtime, docs MCP, RL trainer, or script intercept
to start those.

## Refuse (this tree)

Proxy Aggregator; visualization MCP; GitNexus MCP; Hermes as MCP picker;
dual mutating directors on one working tree; copying any user MCP
catalog into the repo; fused Gortex workspace / hardcoded OCS pin;
silent prompt MITM; `qr` as LLM HTTP path; secrets in `mcp.json`;
`irm | iex`; org/employer Sonar; in-CLI WASM/PyO3; WASM token filter;
shell intercept; RL gym / OPD / weight updates; Context7 cache gateway;
file-sync / memory MCP between hosts; Rekal / Claim Plane / CoAgent as
`qr` subcommands; `escalation-gate` / model cascade as a `qr` command.
