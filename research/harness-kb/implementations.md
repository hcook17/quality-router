# Implementations of evidence-backed patterns

The KB scores papers. This file scores code: Gortex, and the
repositories that evidence and hypothesis papers link to. Checked
2026-10-06 against the GitHub API (read-only) and each project's own
docs. A project's own benchmark is a claim, not KB evidence.

Verdicts: **adopt** (configure as below), **borrow** (copy the pattern,
not the code), **no** (conflicts with evidence or with `AGENTS.md`).

## Gortex (`zzet/gortex`)

Apache-2.0, created 2026-04, v0.64.7 on 2026-10-04. A tree-sitter code
graph with optional LSP confirmation (jdtls for Java), served as a
daemon over MCP, CLI and HTTP. Its cross-repo contract matcher is the
only tool found that addresses P27 (no paper evaluates it).

**Its own evidence.** `BENCHMARK.md` measures tokens and retrieval
recall against ripgrep on Gortex's own query sets. `BENCHMARK-SWE.md`
has no results yet ("Last run: TBD"). There is no task-outcome
evidence. Retrieval-level gains do not predict end-to-end results
(2605.11051), and injected candidates hurt unless precision is high
(2608.05886).

| Gortex feature | KB evidence | Verdict |
| --- | --- | --- |
| Cross-repo contracts: Spring `@*Mapping` routes ↔ RestTemplate/WebClient calls, OpenAPI paths, orphan and mismatch check | P27 has none; deterministic sensors are the supported frame | **adopt** as a read-only cross-repo sensor next to `qr contracts`, which owns the schema diff |
| `verify_change`: signature change vs all callers and implementors | 2608.20167, 2606.24446: verify mechanically | **adopt** |
| jdtls confirms or rebinds edges via references/definition | 2607.25431: live LSP for references (static matched only 64%) | **adopt** (install jdtls) |
| `facade-v1`: 21 tools, ≤15 KB `tools/list` | No evidence paper: 2607.15593 (~15 inlined tools still select well) was rejected in the full audit; the small catalog is `AGENTS.md` policy | **adopt** the facade on policy grounds; do not expose the 178-tool preset |
| Hook mode `deny` (default): blocks Read/Grep/Glob/Bash and redirects to Gortex | 2605.16352: anchor on lexical hits; 2608.24188: keep a byte-exact read path; 2609.00006: production hosts retrieve lexically | **no**. Use `--hook-mode=enrich` |
| Semantic search on by default (GloVe + BM25 fusion) | 2608.26031: code embedding indexes are poisonable; 2606.11864: snippet embedders localize poorly on Java | **no**. Set it to `off` (BM25/FTS5 only) |
| `gortex init --skills` (on by default): per-community SKILL.md plus routing in instruction files | 2606.21926: always-on injection did worse than none; `phase-2-init.md` forbids skill packs | **no**. Turn it off |
| Development memories (`store_memory` …) in the graph store | 2607.17619: durable preferences belong in committed, reviewed files | **no**. Committed `notebook_*` entries are acceptable |
| `audit_agent_config`: stale references in AGENTS.md | Hypothesis only (2606.09090, 2606.15828) | Duplicates `qr lint instructions`; optional |
| `get_untested_symbols` / `get_test_targets` (static reachability) | 2607.18057: *executed* changed-line coverage | Not a substitute for JaCoCo diff coverage |
| Incremental index plus reconcile janitor | 2607.25431: incremental symbol-graph repair matched a full rebuild on 13 of 24 changes | Do a full reindex before trusting a cross-repo contract result in CI |
| Install via `curl \| sh` / `irm \| iex` | `AGENTS.md`: no `irm \| iex` | Use the signed package (Homebrew, .deb/.rpm, scoop) |
| Web UI graph | `AGENTS.md`: no visualization MCP | Ignore |

**Gaps for this team.**
- **Java Kafka:** the built-in topic patterns cover Go, TypeScript,
  JavaScript and Python. `@KafkaListener` and `KafkaTemplate.send` are
  not detected unless they are declared as config-driven event-bus
  boundaries in `.gortex.yaml`.
- **Feign / `@HttpExchange`:** these clients are not in the HTTP
  client extractors.
- **Avro / AsyncAPI:** not contract types in Gortex.
  `qr contracts check` stays the schema gate.

`qr init --graph gortex` stamps the adopt/no verdicts above that live in
`.gortex.yaml` (embedding off, `facade-v1` in hide mode, read-only
`cross_workspace_deps`, `@KafkaListener` / `kafkaTemplate.send`
boundaries) and prints the install-time ones (`--hook-mode=enrich`,
`--no-skills`, jdtls). The Kafka producer matches the `kafkaTemplate.send`
call suffix only; add an `event_bus` entry for another field name.

**Pilot before relying on it.** Run `qr eval` with Gortex on and off,
on the same host, version and model, over your own Java tasks. Record
resolve rate and tokens (2607.03691), because Gortex has published
neither.

## Paper repositories

Of 80 evidence and hypothesis papers that link to GitHub, the table
lists the repos that are the paper's own artifact and could be reused.
The rest are benchmarks, replication packages without a license, or
links to other projects.

| Repo | Paper (status) | License | What it is | Verdict |
| --- | --- | --- | --- | --- |
| `columbia/neo` | 2605.15569 (E) | Apache-2.0 | CodeQL call/data-flow graphs stitched across services, plus an LLM judging authz checks on each path | **borrow** the typed-query pattern for delivery-API authz review. The CodeQL CLI is licensed only for OSS and research; private repos need GitHub Advanced Security |
| `flyersworder/agentic-data-contracts` | 2609.22259 (E) | MIT, on PyPI, active | YAML domain contract: field and metric meanings, forbidden SQL, budgets | **borrow** the contract shape for content semantics. Adopt the library only if agents query the content store with SQL |
| `yxwan123/TDD` (TDDev) | 2605.17242 (E) | MIT | Acceptance-test-first loop as an MCP server, for full-stack web apps with Playwright | **borrow**: re-run the full suite each round and keep the best checkpoint. The code targets web front ends, not Java services |
| `ml-postech/Librarian` | 2605.27787 (E) | MIT | Persistent lookup-only search subagent; research harness on vLLM | **borrow**: define it as a host subagent that returns file:line pointers. No code needed |
| `Paritok-official/paritok-4b-v1` | 2608.24188 (E, authors' product) | Apache-2.0 | Compression proxy between agent and LLM | **no**: it sits on the LLM path. The paper's own result is that compression saves money only below a break-even cost and tripled patch-apply failures at 96% extractive |
| `LanceZPF/agent-as-a-router` | 2606.22902 (E) | MIT | Model router | **no**: model choice is the host's (`AGENTS.md`). Borrow the "static best-model table from your own outcomes" idea if the host routes |
| `omnigent-ai/omnigent`, `pydantic/pydantic-ai-harness` | 2609.00006 (E, inventory only) | Apache-2.0 / MIT | Meta-harnesses and hosts | Out of scope. They are agent hosts (Job A), not `qr`, and the paper measured their contents, not their performance |
| `OpenMOSS/SWE-bench-Science`, `steven1518/vex-bench`, `cjj826/LongJudgeBench` | 2608.19799, 2609.08040, 2606.01629 (E) | MIT | Benchmarks | **borrow** the methods (hidden validators, golden-reference judging) for `qr eval` tasks |

## Established tools the evidence points at

The window applies to research, not tools. These predate 2026, but
evidence papers from the window name them as the mechanism.

| Tool | Paper (E) | Finding | In `qr` today |
| --- | --- | --- | --- |
| japicmp / revapi | 2608.20167 | 95% of what LLM-written client tests caught on dependency bumps was crash-type breakage (missing classes and methods), the class japicmp reports; japicmp itself was not measured | `qr gate api-compat` reads japicmp XML (revapi not read) |
| JavaParser | 2606.24446 | Agent codemods have a higher verified fix rate on JavaParser than on Spoon | Docs only |
| PIT with custom mutators | 2607.11573 | Generic mutation score misranks; build mutators from historical bug classes | Docs only |
| Jazzer / jqwik | 2605.27531 | Fuzzing rejected 8% of unit-test-passing inferred contracts | jqwik recognised by the oracle gate |
| Testcontainers | 2605.06445 | Data-layer failures dominate backend agent errors | Docs only |
| JaCoCo | 2607.18057 | Gate on executed changed lines | `qr gate diff-coverage` |
