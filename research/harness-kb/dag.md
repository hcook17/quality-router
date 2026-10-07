# Would a DAG help this team?

Short answer: **yes for a fixed, deterministic graph around the agent,
no for a graph runtime or a model-drawn task graph as the default way
of coding.** The team already has the useful kind: the SDD stages, CI
gates and the provider-first order across repos. Write those down as
code and config, and let each node run an ordinary bounded agent loop.

Evidence base: 38 papers added for this question (topics T59–T61 plus 8
supplementary picks), 13 existing evidence papers re-tagged, every
evidence paper blind-audited. Patterns P36 (static workflow graph) and
P37 (model-generated task DAG) were added to `taxonomy.json`.
Regenerate: `python3 etl.py load && python3 etl.py report && python3
etl.py robustness`. Status after both gates: **E** evidence,
**H** hypothesis only, **R** rejected.

| Pattern | Supports / contradicts / mixed (evidence papers) | Label (`kb_robustness.md`) |
| --- | --- | --- |
| P36 Static workflow graph / state machine | 2 / 0 / 8 | conditional |
| P37 Model-generated task DAG | 2 / 0 / 2 | leaning |
| P13 Planner-executor (for comparison) | 5 / 0 / 5 | consensus |
| P10 Single-agent loop (for comparison) | 0 / 0 / 4 | unresolved |

Neither DAG pattern is consensus. Both labels survive the September 30
cutoff unchanged. No paper tests either across a team's own
repositories. Only one paper touches Java: ORCA (2608.17018) includes
100 synthetic Train-Ticket Java faults, where the telemetry signal is
weak and the authors ask for caution. On Java, P36 rests on that one
paper, and P37 has no Java evidence.

## "DAG" means four different things here

### 1. A fixed graph of stages and gates, written by the team (P36)

What the evidence says:

- **It wins when deterministic steps do the narrowing.** ORCA
  (2608.17018, E) runs a fixed pipeline: fault signature → fault
  localization → bounded repair → a four-check verifier. It beat an
  open agent loop on the same model: 113 vs 74 valid patches on 150
  real incidents, at 26k vs 640k tokens. Both got the same fault
  signature. However, the baseline ran with a generic SWE-bench-style
  setup, and the benchmark is the authors' own. In Repo0 (2608.19854,
  E), deterministic cohesion and coupling thresholds decide when to
  restructure. That beat letting the model decide.
- **It loses on open-ended, multi-file work.** On one model, an
  Agentless-style pipeline matched agent loops on LocBench (Acc@5 68.9
  vs 70.7) but fell far behind on multi-file MuLocBench (28.9 vs 46.6),
  at roughly half to a third of the estimated cost (2605.16352, E). A fixed
  repair pipeline solved more web-accessibility bugs (72.7% vs 61.5%
  and 59.0%) but caused more side effects (41 vs 28 and 13)
  (2606.21926, E).
- **Scripted handoffs happen, but cost more.** A model-directed team
  realized its declared organization in only 47.2% of runs. A
  code-scripted two-coder workflow guaranteed it and gained +14.2 on
  DeepSWE (p = 0.0025). The +3.4 on Terminal-Bench was not
  significant, and the workflow used 1.7–3.0× the tokens (2609.38345,
  E).
- **Pick one workflow per task type; don't search one per request.**
  A fixed workflow per task type matched per-request generated
  workflows at up to about 12× fewer tokens (2609.38294, E). One simple
  fixed workflow beat both a searched workflow and a routed bank, and
  single-call chain-of-thought tied the bank (2610.07851, E).
- **Production harnesses don't use graph runtimes.** All 11 production
  coding harnesses surveyed run iterative loops, and none uses LangGraph
  or similar (2609.00006, E).
- **The shape matters less than what each node gets.** In GxP-Agent
  (2608.16890, H), the same 15-node topology with generic prompts
  produced 0% of target fields. What worked was each step's slice of
  the spec, its expected outputs and a retry on validation.

### 2. A task DAG that the model draws at run time (P37)

- **Drawn upfront, it is no better than a loop.** A full upfront DAG
  scored 43.7, against 43.0 for plain ReAct averaged over three
  benchmarks. Growing the DAG a few nodes at a time from evaluated
  results scored 55.9, on the same model and tools (2609.39154, E;
  deep-research tasks, not code).
- **Model-drawn edges are unreliable.**
  - Agent plan DAGs recovered the reference dependencies with edge F1
    of 0.27–0.71. Closed harnesses stayed near the concurrency budget,
    and open ones collapsed to chains (2608.00267, E).
  - Models picked the right nodes but mis-emitted attributes and
    boolean structure as graphs got denser (2608.30250, E).
  - Inferring edges from call order was wrong for about 42% of adjacent
    pairs (2608.02680, E).
- **Declared edges also need checking.** Generated tests never
  exercised many developer-declared handoff edges: 10 of 41 delegations
  and 20 of 65 tool edges (2605.26521, H).
- **Parallel DAG workers pay off only on very long tasks.** Below
  about 1M single-agent tokens, a model-grown DAG was slower and used
  about 9–15× the tokens. Above it, wall-clock time roughly halved at
  about 3.7× the tokens (2609.32700, E). There was no baseline of N
  parallel single agents at equal budget.
- **The test step must not see the implementation.** Generating tests
  after the same model saw its own code cut fault detection by about
  8–18 points across 5 models. With the prompt plus the code, the drop
  was 9.1–18.2 points, a claim rated strong. Adding the spec alongside
  the code did not recover it (2607.05139, E). In any graph, an edge
  from implementation to test generation is a defect.

### 3. A graph framework (LangGraph, n8n, Dify) as the harness

- **No speed advantage.** An auto-parallelizing compiler ran the same
  5 workflows 2.0–3.2× faster (geometric mean) than seven graph
  frameworks. Part of the gain came from parallelism the framework
  versions never expressed, and hand-parallelized code was faster still
  (2605.18697, E). Concurrency belongs in ordinary code: in Java,
  `CompletableFuture` or virtual threads.
- **A declared graph is auditable, but it is not a trust boundary.**
  - In 84.5% of 496 confirmed injection cases, an edge passed
    free-form agent output into a later shell, gh or git step
    (2605.07135, E).
  - Comment-based and label-based guards on edges were satisfied by
    outsiders, and an allowlisted shell still read secrets through
    `/proc` (2605.11229, E).
- **The guide papers have no evidence.** The LangGraph pathways paper
  (2607.19297) and the declarative-primitives paper Credo (2608.27790)
  were both rejected: one has no evaluation, the other no coding tasks
  and no code.

### 4. The dependency graph between repositories and contracts

This DAG is deterministic: it is computed, not drawn by a model. `qr
contracts check` already derives a provider-first merge order from the
manifest and warns on cycles. Cross-repo coordination (P27) is still
unstudied, at 0 supporting and 3 mixed papers, so this stays an
engineering decision.

## What to do

1. **Keep the outer graph deterministic and in git.** That means the
   SDD stages, the `qr init --ci` workflow, and the phase-4/6 order:
   spec → separate test author → `qr spec lock` → implement →
   `qr gate acceptance` and a held-out run. Gates should read git and
   CI, not what the agent reports about itself (2606.26924, E: its
   gates only see agent-reported state).
2. **Make each node a bounded agent loop, with artifacts as the
   edges.** Pass files such as the spec, the lock and reports, not
   transcripts or free-form agent text. Validate typed outputs before
   any shell or git step uses them (2605.07135).
3. **Encode ordering and isolation constraints as edges.** Test
   generation reads the spec, never the implementation (2607.05139).
   Merge providers before consumers (`qr contracts check`).
4. **Don't adopt a graph runtime for coding.** It adds no capability or
   speed, and it is one more constituent to keep removable.
5. **Pilot model-drawn DAGs only for long, multi-part work**, such as a
   schema change that touches all four repos. Grow the DAG
   incrementally, check it mechanically (acyclic, edges equal data
   dependencies, every criterion covered), and compare it with `qr
   eval` against one agent and against N parallel agents at the same
   budget.

## What would change this answer

- A same-model comparison on multi-file Java or multi-repo tasks where
  a fixed graph beats the open loop on resolve rate, not just on cost.
- A model-drawn DAG that beats N parallel single agents at equal token
  budget on coding tasks.
- Field data from a team running a graph runtime as its coding harness.
  None was found.

## Where `qr` could help (not built)

- **`qr plan check`:** deterministic checks on a task plan, whether
  written by an agent or a human. It would reject cycles, uncovered
  `AC-n` criteria, test tasks that depend on implementation tasks,
  and cross-repo tasks out of provider-first order. Evidence:
  2608.00267, 2608.30250, 2607.05139; 2605.26521 is H.
- **`qr lint workflows`:** flag CI jobs where agent-step output flows
  into a shell, gh or git step, or where an externally triggered agent
  job holds long-lived secrets. Evidence: 2605.07135, 2605.11229.

Either would be built the same way as phase 6: spec, a separate test
author, lock, implement, then a held-out check.
