# Phase 3: harness gates for multi-repo Java teams (spec gate)

**Status:** implemented under `src/quality_router/harness/` + `tests/harness/`.
Architecture lock: `docs/research/architecture-decisions.md`. Evidence:
`research/harness-kb/FINDINGS.md`. End-to-end demo:
`examples/content-pipeline/run-demo.sh`.

## Goal

Turn the KB's supported findings into deterministic predicates that any
agent host and any CI can call. The agent proposes a change; the repo's
build produces artifacts (JaCoCo XML, sources, contracts); `qr` reads
those artifacts and passes or fails the change. `qr` never builds, never
launches an agent, and never writes to a repo other than the one it was
pointed at.

## Commands

All commands: exit 0 pass, 1 gate failed, 2 usage error (with an example
on stderr). `--json` prints `{gate, passed, errors, warnings, summary,
findings[]}`. `--strict` (where offered) also fails on warnings.

| Command | Reads | Fails when |
| --- | --- | --- |
| `qr gate diff-coverage --base REF --jacoco GLOB [--min 0.8] [--catch-min X]` | `git diff REF...HEAD` (or `--diff FILE\|-`), jacoco.xml per module | Covered/executable changed lines < `--min`; changed catch-block coverage < `--catch-min` (otherwise uncovered catch lines warn). Test sources excluded unless `--include-tests`. |
| `qr gate test-oracles --base REF \| --paths F...` | Changed JUnit 4/5/jqwik test methods | A changed test has only null/boolean/no-throw assertions (`weak`), only Mockito `verify*` (`mock_only`), or none. `--allow-weak` downgrades weak to a warning; `--assert-helper NAME` counts project helpers as strong. |
| `qr lint instructions [--root .] [--max-lines 150]` | AGENTS.md, CLAUDE.md, GEMINI.md, copilot/cursor rules | A backticked path or FQCN does not exist at HEAD (build-output dirs are skipped). Warns on bloat, security prohibitions with no `policy.json` entry, host files that do not import `@AGENTS.md`; info on style rules that belong in a formatter. |
| `qr spec trace --spec F... --tests DIR...` | Spec markdown; test sources in any number of checkouts | An acceptance-criterion id (`AC-n`, `--id-pattern`) is referenced by no test. Warns on MUST/SHALL lines with no AC id or `[check: …]` tag, and on more than `--max-constraints` per spec. Summary carries the trace map. |
| `qr contracts diff --old P\|git:REF:P --new P [--role output\|input] [--avro-mode M]` | Two JSON Schema, OpenAPI 3 (JSON) or Avro documents | Any breaking change for the role (see rules below). Kinds must match. YAML is rejected (stdlib only); export JSON. |
| `qr contracts check --manifest contracts.json [--checkouts DIR]` | The coordination repo's manifest and every listed checkout, read-only | A consumer's vendored copy is incompatible with the provider (`consumer_breaking_drift`), or a repo or contract is missing. Warns on stale-but-compatible copies and provider/consumer cycles. Summary carries a provider-first merge order. |
| `qr policy check --command C \| --path P` | `.quality-router/policy.json` | The command or path is denied. |
| `qr policy hook --host cursor\|claude-code [--audit F]` | Hook JSON on stdin | Speaks the host's protocol: Cursor gets `{"permission": "deny", …}` on stdout (exit 0); Claude Code gets exit 2 and the reason on stderr. |
| `qr eval prepare --repo R --base C --task-id T --out D [--hidden P]... [--dry-run]` | One checkout | Writes `D/workspace` (single snapshot commit, no history, no remotes), `D/hidden` (withheld tests, sha256 in `task.json`). |
| `qr eval report --runs runs.jsonl [--baseline host@ver/model]` | One JSON line per run | Resolve rate drops by more than `--max-rate-drop` with disjoint Wilson 95% CIs (error; overlapping CIs warn), or tokens per resolved task rise by more than `--max-token-increase`. |
| `qr init --policy [--host cursor\|claude-code]` | — | Stamps `policy.json`; with a host, merges `qr policy hook` into `.cursor/hooks.json` (`beforeShellExecution`, `beforeReadFile`, `preToolUse` Write\|Delete; all `failClosed`) or `.claude/settings.json` (`PreToolUse`). Idempotent; never `mcp.json`. |
| `qr init --ci github-maven` | — | Stamps `.github/workflows/qr-harness.yml` (`mvn -B verify`, then the gates). Never overwrites. |

### Contract rules

- JSON Schema, role `output` (we produce, consumers read; delivery API,
  normalized events): removing a property, making one optional, widening a
  type, adding a property to a closed object → error. New enum values warn
  (exhaustive `switch` consumers). Loosened bounds warn.
- JSON Schema, role `input` (we accept; service endpoints): new required
  property, newly required existing property, narrowed type, removed enum
  value, introduced enum, tightened bound, closing `additionalProperties`
  → error. `integer → number` is compatible.
- OpenAPI: removed operation, removed 2xx response or media type, new
  required parameter or request body → error. Request schemas are diffed
  as `input`, response schemas as `output`; `$ref` is resolved.
- Avro: reader/writer resolution per the spec. `backward` = new reader,
  old data; `forward` = old reader, new data; `full` = both. Field without
  default, non-promotable type change, unreadable union branch, enum
  symbol without reader default → error. Aliases and named-type
  namespaces are honoured.

## Evidence map

Only KB evidence papers are cited: papers that passed the date audit,
the review gate and the contribution gate (`research/harness-kb/`).
Hypothesis-only support is labelled as such.

| Gate | Finding it encodes |
| --- | --- |
| diff-coverage | 2607.18057: tests executed 61.5% of agent-changed Java lines. A green `mvn test` is not evidence the change executed. 2608.25939: an agentic harness raised pass rate while, on PHP, direct invocation of the focal method fell from 98.9% to 27.6%. |
| test-oracles | 2606.18168: 80% of agent test-file patches carry weak or no oracle. 2608.20167: among generated tests that reached a broken API and still passed, catch blocks (32 of 80 sampled) and silent null fallbacks (37) hid the break. 2608.16742 / 2608.19799: self-consistent wrong tests; keep hidden validators. |
| lint instructions | Enforcement: 2608.23550 (about 4–16% of CLAUDE.md security rules have an enforcing control). Brevity: 2606.21926 (always-on standards text did worse than no guidance). The stale-reference and bloat checks are **hypothesis only** (2606.09090, 2606.15828, 2607.27250): cheap and deterministic, not proven to help. |
| spec trace | Per-target acceptance tests (2605.15846); acceptance tests kept as regression obligations (2608.00267); restate frozen criteria at completion (2607.17937). 2605.06445: constraint decay. SDD as a methodology is unsupported; the trace makes the spec checkable. |
| contracts | No direct evidence on agents coordinating across a team's own repos (P27). Closest: verify mechanically. 95% of what LLM-written client tests caught on dependency bumps was crash-type breakage that a static diff finds (2608.20167; japicmp itself not measured); AST edits validated against the target artifact (2606.24446, 2608.30497). |
| policy | 2608.23550 (prose is not policy), 2609.22259 (declared forbidden operations stopped mutating SQL), 2609.08149 (egress blocking closes leakage), 2607.07405 (deterministic predicate before writes; audit gate precision). |
| eval | 2607.03691 (one harness across releases: ~70% token rise with no resolve gain; 12.3% flips, so a small probe detects cost regressions only), 2606.12344 (mature harnesses within ~2 pp; a weak one lost up to 24 pp), 2609.08149 / 2606.12344 (future git objects and visible tests inflate scores), 2607.08964 (weighted sub-checks, not binary pass). |

## Invariants (must hold)

- Reads reports; never runs Maven/Gradle or relays their output. CI (or
  the developer) builds; `qr` gates.
- Cross-repo commands (`spec trace`, `contracts check`) read other
  checkouts and write nothing. No orchestration, no worktree sync.
- Deterministic Python predicates; no model call anywhere in `harness/`.
- Disconnected constituent no-ops: no `policy.json` → hook allows. A
  present-but-invalid policy or an unparseable payload → hook denies
  (fail closed). Host hook entries are `failClosed`.
- Host wiring touches only the host's hooks file. Never `mcp.json`, never
  LLM base URLs, never tokens.
- Stdlib only (no new runtime deps; `uv.lock` unchanged).

## Known limits

- The Java scanner is lexical, not a parser: it blanks strings/comments and
  matches braces. Text blocks with unbalanced braces can confuse it.
- `test-oracles` judges assertion *kind*, not correctness. Mutation testing
  (PIT) is the stronger, slower check; run it in CI if the budget allows.
- No AsyncAPI or Protobuf yet; YAML contracts must be exported to JSON.
- `contracts check` compares vendored copies. It cannot see a consumer that
  deserializes without a vendored schema; list those consumers anyway.

## Verify

- `uv run pytest --cov` (floor 98.7%), `uv run ruff check src tests`.
- `examples/content-pipeline/run-demo.sh`: the review fix passes every
  gate. Since phase 4 the agent PR fails five of seven (the scaffolded
  acceptance tests now cover its catch path, so diff coverage passes, and
  every criterion is traced); see `phase-4-acceptance-first-sdd.md`.
