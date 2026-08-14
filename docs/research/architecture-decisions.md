# Architecture lock

One-page C4 + job table. Spec SoT for commands: `docs/design/phase-1-cli.md` and `docs/design/phase-2-init.md`.

## Agent host (do not lock)

`qr` does not require Cursor, VS Code, Claude Code, Windsurf, or any
other IDE/agent runtime. The user already has an agent host; that host
talks **directly** to constituent MCPs. `qr` verifies/installs/stamps.

Optional `--host …` adapters at `qr init` time may write that host’s
rule/hook files. Portable stamps (rule text, git hooks,
`.quality-router/gitnexus-hooks.off`) always work without an adapter.

## Three jobs (do not fuse)

| Job | Owner | Not |
| --- | --- | --- |
| A. Cheap vs expensive **model** | The agent host the user already runs (Cursor Router, Claude Code, Copilot, …), or a later sibling host | A second cascade in front of MCP; `qr` MITM of prompts; Ollama as a silent interceptor |
| B. Which **MCP / tool** fires | Deterministic `qr` + rules + scoped tool listing | Local LLM as Proxy Aggregator |
| C. Two agent **runtimes** driving one checkout | Refuse | Two directors (for example Hermes **plus** an IDE agent) on the same tree |

Job C is “do not dual-host two directors.” It is not “you must use Cursor.”

Ollama is an inference backend a host may **opt** at via base URL. Hermes
is another host (ACP) or extra MCP tools — not a MITM of another host’s
paid model. Tool/MCP audit logs belong on the **director host** (local
JSONL), not as a `qr` proxy in front of MCP, and not as Langfuse Cloud
as SoT.

## C4 (skip Code)

- **C1 Context:** You use `quality-router` and *an* agent host. `qr`
  wraps `~/dev/local-quality` and stamps portable (plus optional host)
  config. The agent host talks **directly** to constituent MCPs.
  Ollama/Hermes is a neighbour with **no** edge Agent → Ollama → Gortex.
- **C2 Containers:** `qr` CLI (verifier), optional host adapters
  (stamps), graph-3d HTML (presentation, not an MCP). The agent host =
  proposer. That host’s router = job A.
- **C3:** `install` / `init` / `status` / SDB gate (catalog cliff ~10–15
  tools; no Gortex+GitNexus+Serena).

## Local brain vs this product

A 27B director that calls a frontier coding agent as a tool is Faraday
[2608.13331](https://arxiv.org/abs/2608.13331) (CAT). A 7B orchestrator
with executor cost profiles is EASY
[2608.04588](https://arxiv.org/abs/2608.04588). A cheap-first tutoring
cascade with evaluator threshold τ is FairTutor
[2606.20713](https://arxiv.org/abs/2606.20713). Those are **sibling**
hosts, not `qr`. Do not put Ollama/Hermes between the agent host and
these MCP servers.

SWE papers invert the split: small explorer, frontier still solves
(FastContext [2606.14066](https://arxiv.org/abs/2606.14066), CodeGrep
[2608.05886](https://arxiv.org/abs/2608.05886), SWE-Pruner Pro
[2607.18213](https://arxiv.org/abs/2607.18213)).

Pre-answer routers recover 7.5–14.4% of a certified 9.7–30.7 pp oracle
gap (Opportunity Is Not Realizability
[2608.08265](https://arxiv.org/abs/2608.08265)). Escalation needs a
declared signal Z and a held-out G_learn certificate, not vibes.

MCP expose-all still fails (SkillWeaver
[2606.18051](https://arxiv.org/abs/2606.18051); Haiku cliff 10–15 tools,
Rodrigues & Vas [2606.30317](https://arxiv.org/abs/2606.30317)). A cloud
gateway that breaks direct-connect
([2607.15593](https://arxiv.org/abs/2607.15593)) is refused here.

## Scope

This uv CLI must `qr init` **any** service. Gortex stays a removable
constituent. Only mediator packaging lives here.

## Phase status

- Phase 1 CLI: implemented (`help` / `status` / `install`). Spec:
  `docs/design/phase-1-cli.md`. Status reports `agent_host_lock=none`.
- Phase 2 `qr init`: spec gated in `docs/design/phase-2-init.md`. Not
  implemented yet. The product is not pinned to one agent host.
