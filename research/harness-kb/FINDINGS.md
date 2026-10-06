# Findings: agentic harness research, May–early October 2026

Scope: arXiv papers **first submitted** (v1) from 2026-05-01 through
2026-10-06, read for a backend Java team that ingests
healthcare-education content across at least four repositories and
delivers it to front-end applications. The team is rolling out
spec-driven development (SDD) through a Research → Frame → Spec → Gate
sprint.

All numbers below come from `kb.sqlite`. Regenerate it with
`python3 etl.py load && python3 etl.py report`. The supporting tables
are in `kb_tables.md`, the per-pattern evidence is in `kb_evidence.md`,
what each paper adds is in `kb_contributions.md`, and the
abstract-level trend counts are in `landscape.md`.

A paper counts as **evidence** only if it passes two deterministic
gates: the review gate (rigor, conflicts of interest, verdict) and the
contribution gate (it adds a transferable heuristic, nuance, design
pattern, anti-pattern, constraint or test practice, backed by at least
moderate evidence, that is not already known). Papers that pass review
but only add volume are listed as hypotheses or dropped. They never
carry weight.

## Bottom line

1. **Evaluate the harness, not just the model, but don't over-read
   small probes.**
   - With the model fixed, mature harnesses landed within about 2 pp
     of each other, while one weak harness lost up to 24 pp
     (2606.12344). Use your own tasks to screen out outliers, not to
     rank the leaders.
   - Across releases of one CLI, token use per task rose about 70%
     with no gain in resolve rate, and functional CI did not catch it
     (2607.03691). But run-to-run flips on identical releases (12.3%)
     were as large as the spread between releases, so a 50-task,
     two-run probe detects cost regressions, not effectiveness
     changes.
   - The advantage of a complex harness over a minimal loop shrank by
     more than half as models improved (2609.32459). Re-measure custom
     components at every model upgrade.
2. **Deterministic sensors are the best-supported investment, and
   "tests pass" is weaker than teams assume.**
   - The execution-verifier loop (P16) has 21 supporting evidence
     papers against 1 contradicting (weighted 5.88 vs 0.22).
   - The same papers show how "green" misleads:
     - existing tests execute only 61.5% of the Java lines agents
       change (2607.18057);
     - 80% of agent test patches carry weak or no oracle (2606.18168);
     - an agentic harness raised pass rate while direct invocation of
       the focal method fell from 98.9% to 27.6% (2608.25939);
     - catch-all try/catch tests were the largest single reason
       generated tests missed breaking changes (2608.20167);
     - agents at about 97% on visible tests pass hidden validators
       less than half the time (2608.19799);
     - with frontier models, compile gates catch almost nothing (4–15%
       of failures), so the behavioural tests carry the whole load
       (2605.15846).
3. **Spec-driven development (P14) as a methodology still has no
   outcome evidence. Specific spec practices do.**
   - Every SDD framework or corpus paper failed one of the gates:
     2609.00252, 2609.24348 and 2608.16618 were rejected, and SpecMine
     (2608.25202) was dropped because it has no outcome measure.
   - Practices that pass both gates:
     - give every spec target its own acceptance test (2605.15846);
     - keep each completed unit's acceptance tests as regression
       obligations (2608.00267);
     - re-run the full acceptance suite each round and keep the best
       checkpoint, not the last one (2605.17242);
     - at completion, restate the frozen acceptance criteria rather
       than saying "double-check" (2607.17937);
     - fully specify the output contract (2609.22222);
     - state the encoding of every default and wildcard (2609.22259).
   - Two cautions. Piling persistence and architecture constraints
     into a backend spec cut behavioural pass rate by about 27 pp
     (2605.06445). Agents' own plans name where to edit far more often
     than how to constrain or validate the change (2608.09072).
4. **Instruction files (P01) now have no evidence either way.**
   - The ablation (2607.27250), the stale-reference study (2606.09090)
     and the AGENTS.md smell catalogue (2606.15828) are hypotheses
     only.
   - What does pass the gates:
     - about 4–16% of CLAUDE.md security rules have a host control
       that enforces them (2608.23550);
     - injecting domain standards text on every call did worse than
       no guidance, and loading it selectively did best (2606.21926);
     - prohibitive rules cut abnormal actions but caused agents to
       abandon legitimate work in 19% of runs (2609.16287);
     - durable preferences belong in committed, reviewed files, not in
       opaque host memory (2607.17619).
5. **Cross-repo coordination (P27), your core problem, remains
   unstudied.** No evidence paper supports or contradicts a cross-repo
   orchestration pattern. The transferable pieces are narrower:
   - agent-authored AST codemods, targeting JavaParser rather than
     Spoon, with regex and pom edits rejected (2606.24446);
   - validating every old→new API mapping against the target artifact
     (2608.30497);
   - typed CodeQL-style queries for cross-service flows in Java
     microservices (2605.15569);
   - grounding each contract-bug alarm in grep-retrieved code
     (2607.00555);
   - japicmp-style static API diffs, which catch 95% of what
     LLM-written client tests catch (2608.20167).
6. **Healthcare and education content is still a research gap.**
   - T56 has 1 evidence paper and T57 has none.
   - Reviewers agreed with 91–94% of an agent's NFR assessments, which
     scored only 0.38 F1 against experts (2606.24834). The same paper
     shows agent requirement-to-code links reach about 0.2 F1 on Java.
   - Agent accessibility repair fully fixed fewer than 26% of files
     and altered the structure of about 30% (2605.27716).

## Method

| Stage | Result |
| --- | --- |
| Research topics | 58 topics in 11 clusters (`taxonomy.json`), each with phrase queries across 11 arXiv categories |
| Harvest | 5,589 unique papers in the window; 3,989 passed the relevance gate |
| Selection | 228 candidates (4 per topic, ranked by relevance; T26/T57 had only 2) plus 12 papers cited by the architecture lock (`etl.py add --reason lock-citation`) |
| Date audit | v1 date and ID prefix both inside the window, rechecked live against arXiv; withdrawn papers rejected (see below) |
| Full text | Read from arXiv HTML, with a pdftotext fallback |
| Pre-review signals | Vendor affiliations, artifact URLs, and limitations/ethics/acknowledgment sections, extracted deterministically |
| Adversarial review | Each paper reviewed against `REVIEW_RUBRIC.md`: 5 scores (0–5), 25 bias codes, COI severity, claim strength, per-pattern stance |
| Blind audit | 59 papers (26% of the harvest selection) independently re-reviewed without seeing the first review. Merged conservatively: lowest score and strictest verdict win |
| Hallucination check | 4,815 numbers cited by reviewers matched against the paper text; 53 (1.1%) not found, mostly derived values |
| Review gate | Deterministic code (`etl.py admission`), not LLM judgment |
| Contribution gate | Each review-passing paper classified against `CONTRIBUTION_RUBRIC.md`, then gated by code (`etl.py contribution_gate`). Contribution strength is capped at the paper's strongest audited claim; the reviewer can only tighten the outcome |

Outcome for the 240 reviews:

| Status | Papers | Mean rigor | Meaning |
| --- | --- | --- | --- |
| Evidence (caveated) | 96 | 2.89 | Passed both gates |
| Hypothesis | 30 | 2.43 | A transferable idea, but on weak evidence, or the paper is self-declared preliminary |
| No contribution | 39 | 2.49 | Restates known practice, duplicates a stronger paper, or does not transfer |
| Rejected | 75 | 1.49 | Failed review: 39 off-topic, 35 on quality, 1 withdrawn |

No paper cleared every check cleanly, and the best scored rigor 4 of
5. Rigor alone does not separate volume papers from useful ones:
dropped papers averaged rigor 2.49, close to the hypotheses. Most were
competent work that told this team nothing new. Treat everything below
as directional evidence, not settled science.

Evidence weight per paper:
`(rigor/5) × (0.6 + 0.4·repro/5) × (1 − 0.12·coi_risk)`, multiplied by
0.6 if caveated and set to 0 for every non-evidence status. The
highest weight in the KB is 0.48.

### Date audit

The window applies to the **first** submission. A paper first posted
before May 2026 and only revised inside the window does not qualify.
`admission` checks the v1 `published` date, and arXiv IDs encode the
v1 month.

| Check | Result |
| --- | --- |
| v1 dates of the 240 reviewed papers | 2026-05-02 … 2026-10-05 |
| v1 before 2026-05-01 | 0 |
| Revised on arXiv since we reviewed them (live recheck) | 0 |
| Withdrawn | 1: 2606.14066, a lock citation, now rejected |
| Self-declared extensions of earlier work | 1, already rejected on quality |
| Self-declared work in progress | 7 flagged `self_declared_incomplete`; capped at hypothesis |

### Contribution audit

Of the 165 papers that passed review, 69 (42%) added nothing the team
can use on adequate evidence. Quantity-over-quality flags:

| Flag | Papers | What it catches |
| --- | --- | --- |
| numbers_without_mechanism | 18 | Gains reported without the ablation that says why |
| system_description_only | 9 | "We built X" with no outcome measure |
| leaderboard_only | 8 | Rankings with no transferable lesson |
| survey_restatement | 7 | Reorganises known advice |
| self_declared_incomplete | 7 | Authors call it preliminary or WIP |
| position_without_evidence | 5 | Argument only |
| renamed_known_idea | 4 | A new name for established practice |

Qualifying contributions from the 96 evidence papers: 38 test
practices, 32 nuances, 24 heuristics, 17 constraints, 16 design
patterns and 15 anti-patterns. Each one is listed in
`kb_contributions.md`.

## Where each pattern lands

Counts are evidence papers only, after the audit merge. "Supp" and
"Contra" are paper counts.

### Consensus: build these

| Pattern | Supp / Contra | What the evidence actually says |
| --- | --- | --- |
| P16 Execution verifier loop | 21 / 1 | Strongest pattern overall. Feed raw javac diagnostics, not LLM-written explanations (2609.00362). Accept a defect claim only with a reproducing failing test (2606.22263). Cap repair retries at about 3 (2609.03086). Benchmark any error-feedback loop against a blind redraw with the same budget: sanitized diagnostics added nothing over resampling in one study (2609.22222). |
| P17 Static analysis in the loop | 7 / 1 | Rule-based compile repair beat LLM repair loops for Java test generation (2607.19682, Huawei, medium COI). Typed CodeQL queries handle cross-service Java flows (2605.15569). Grounding contract alarms in retrieved code cut false positives from 60.5% to 13.9% (2607.00555). |
| P05 Lexical/deterministic retrieval | 8 / 0 | Production harnesses retrieve with ripgrep, glob and tree-sitter, and use LSP for post-write diagnostics (2609.00006). Serve definitions from a static graph and references from a live LSP (2607.25431). Expand grep hits to structural neighbours rather than going graph-first (2605.16352). |
| P21 Policy-as-code guardrails | 7 / 0 | Declared forbidden operations stopped mutating SQL (2609.22259). Blocking egress closed leakage channels (2609.08149). Put a deterministic predicate in front of write tools, and audit each gate's precision by minus-one removal (2607.07405). Route by enrolled IDs, never display names (2609.27624). |
| P24 Token and cost budgets | 7 / 0 | Output tokens cost 30–1,000x more energy than input on self-hosted models (2605.27787). Do the break-even arithmetic before adding a paid compressor (2608.24188) or codifying a procedure (2610.02932). |
| P34 Structured acceptance criteria | 4 / 0 | A fully specified output contract (2609.22222). Acceptance-test-first repair, keeping the best checkpoint (2605.17242). Under-specified defaults (2609.08149, 2609.22259). Per-target acceptance tests (2605.15846). |
| P30 Observability and audit | 5 / 0 | Merge rate is a confounded KPI: record closure reasons and reviewer touch (2605.22534). Count the invoking developer as the author: 40.1% of agent PRs get no independent review (2607.07980). Log whether a declared multi-agent workflow actually happened (2609.38345). |
| P13 Planner-executor | 6 / 0 | Plan verification together with implementation (2608.09277). A plan → develop → independent-test loop beat plain continuation at fewer tokens (2609.01481). Hand off through artifact files, not transcripts (2608.25457). |
| P35 Formal and independent checkers | 6 / 0 | Gate agent transforms with a small trusted checker (2605.08927). Fuzz agent-inferred contracts and reject trivially true ones (2605.27531). Run differential campaigns against a reference (2607.28928). |
| P12 Task-specific subagents | 2 / 0 | A persistent lookup-only search subagent returning file:line pointers (2605.27787). Pre-inject retrieved files only when retriever precision is high (2608.05886). |

### Contested: use narrowly and measure

| Pattern | Supp / Contra | Why it is contested |
| --- | --- | --- |
| P18 LLM-as-judge or AI reviewer | 3 / 2 (12 mixed) | Mean judge accuracy is 0.56 on long-form outputs. Golden references help; rubrics on top of them don't (2606.01629). Style edits raised judge scores in more than 65% of attempts (2605.26156). Per-task hidden rubrics reached τ≈0.19 against experts (2608.13331). Ericsson's per-dimension reviewers reached 96% author-rated precision on few commits (2609.15877). Advisory only. |
| P08 Context compaction | 1 / 3 (8 mixed) | Single-shot retention scores do not predict end-to-end runs: 7 vs 19 resolved (2605.11051). If you compress, keep it extractive and keep a byte-exact read path for files being edited (2608.24188). Refresh repo maps only when focus shifts (2609.16936). |
| P11 Multi-agent role teams | 0 / 2 (4 mixed) | Generic role teams hurt (2609.32459). An orchestrator with full tools never delegated, so give it read-only tools (2609.38345). The two-agent ceiling (2608.23740) is a hypothesis only. |
| P06 Embedding RAG over code | 3 / 2 | No pinned production harness uses code embeddings (2609.00006). Snippet leaderboards do not predict localization, and BM25 beats several dense models on Java (2606.11864). Code embedding indexes are poisonable (2608.26031). |
| P02 Skills and progressive disclosure | 4 / 1 (9 mixed) | Selective loading beats always-on (2606.21926). Lint AI-written SKILL.md files for portability and safety (2608.08453). Scanners miss split-intent skill attacks (2606.14154). A registry needs procedural skills alongside it (2607.16617). |
| P23 Model routing | 3 / 2 | Per-stage routing works (2606.22263). Cheaper models faked 6 of 39 reproductions (2607.25333). Oracle-gap numbers are upper bounds (2608.08265). A static best-model table built from your own outcomes matches an LLM router (2606.22902). Routing remains the host's decision (see AGENTS.md). |
| P15 TDD with agents | 2 / 0 (3 mixed) | The main failure is code and self-written tests agreeing on the same wrong behaviour: keep a hidden oracle (2608.16742). Mutation score is not bug finding: the top mutation scorer found 25.6 pp fewer real bugs (2607.11573). |
| P26 Self-improving harness | 1 / 2 | Self-authored verification is unreliable (2607.24300). Agents tamper with their own harness (2609.00069). Require graded predictions for harness changes (2609.01861). |
| P04 MCP | 1 / 1 | About 10% of tool descriptions misrepresent the code (2606.04769). Conformance-test in-house servers (2606.05339). Taint-scan for leaks (2606.21338). Check the host's tool-name collision policy (2609.27624). |

### Unsupported or unstudied: do not budget for these as quality levers

| Pattern | Supp / Contra | Status |
| --- | --- | --- |
| P01 Instruction files | 0 / 0 | No evidence paper. All three AGENTS.md papers are hypotheses. Treat the files as operational hints only. |
| P14 Spec-driven development as a methodology | 2 / 0 (3 mixed) | The two supports are about verification planning (2608.09277) and specification-guided model checking (2607.25333), not SDD adoption. The Google contracts paper (2608.17177, medium COI) shows gains only at k≥4 attempts, for about 38% more tokens. |
| P27 Cross-repo coordination | 0 / 0 (3 mixed) | No direct evidence. |
| P29 Parallel agents in worktrees | 1 / 0 | Thin. |
| P22 Prompt-injection defenses | 1 / 0 | Tree-sitter neutralisation of untrusted code cut injection about 3x but left 6–8% (2606.19235). Never write "follow the instructions in this document" for untrusted content (2608.06477). |
| P28 Deterministic codemods | 1 / 0 | One paper (2606.24446), but it is Java-specific and direct. |

## Hypotheses worth testing locally

These papers passed review but not the contribution gate. Their ideas
are plausible and cheap to try, but they are not evidence.

| Idea | Paper | Why it is only a hypothesis |
| --- | --- | --- |
| Write AGENTS.md as operational warnings ("the full suite is slow; run the module's tests") | 2607.27250 | 4 tasks on 1 repo; the correctness null restates earlier work |
| CI check that AGENTS.md references exist at HEAD | 2606.09090 | Renamed documentation drift; the impact on agents is future work |
| Lint AGENTS.md for style rules already enforced by tools | 2606.15828 | Distilled from grey literature; prevalence only |
| Never rename from LSP references alone; use an LSP only where grep is noisy | 2608.13568 | Self-declared preliminary, tiny N |
| At most two concurrent agents per codebase | 2608.23740 | Every claim weak after audit |
| Normalise token accounting before comparing host cost | 2607.22585 | Single-trial, non-comparable measurements |
| Scoped MCP proxy, and a 10–15 tool cliff | 2606.30317 | Position paper with Haiku-only telemetry |

Full list: `kb_tables.md` → "Hypotheses (not evidence)".

## Theories and frames that recur

- **The harness as a hidden variable, with noisy measurement.** The
  harness matters (2606.12344, 2607.03691, 2609.32459), but
  run-to-run variance is as large as many reported gaps. Binary
  grading hides partial progress in 63% of runs, so use weighted
  deterministic sub-checks (2607.08964).
- **Guides vs. sensors.** Guides are weak or harmful when always on:
  instruction files, always-on standards text (2606.21926), generic
  "improve observability" prompts (2607.05785) and self-critique steps
  without tests (2606.25195). Sensors are strong. The asymmetry
  favours spending on sensors.
- **Constraint decay.** Each added prose constraint raises the failure
  rate, and failures concentrate in the data layer, so test against
  the real database engine (2605.06445). This matters for ingestion
  code, which is mostly data-layer code.
- **Self-consistent wrongness.** When the same agent writes the code
  and the tests, they agree on wrong behaviour (2608.16742, 2607.24300).
  Hidden harness-owned oracles (2608.19799) and fresh post-commit
  samples (2610.02952) are the remedies.
- **Comprehension debt.** Agent users recall less of their own code
  (2607.26375). In mature Java repos, smell counts stayed flat while
  LOC grew about 13%, so report raw counts as well as densities
  (2606.13298).
- **Benchmark leakage.** Strip future commits and the reference fix
  from internal eval images (2606.12344, 2609.08149). Re-host mined
  tasks on current main (2607.28591).

## Biases and conflicts of interest in the literature

Bias codes across the 240 reviewed papers:

| Bias | Papers | Share |
| --- | --- | --- |
| No variance reported | 117 | 49% |
| Small sample | 107 | 45% |
| Self-evaluation (authors' own system and metric) | 107 | 45% |
| Metric does not measure the claim | 103 | 43% |
| Closed artifacts | 80 | 33% |
| Hype language | 66 | 28% |
| Single model | 61 | 25% |
| Strawman baseline | 57 | 24% |
| Contamination risk | 57 | 24% |
| Unvalidated LLM judge | 56 | 23% |

- **Conflicts of interest.**
  - 10 papers had a high COI: 7 rejected, 1 hypothesis, 2 evidence.
  - 17 had a medium COI: 7 rejected, 5 hypothesis or no
    contribution, 5 evidence.
  - High- and medium-COI papers averaged rigor of about 1.8, against
    about 2.4 for low or no COI.
- **Claim strength.** Of 1,014 claims extracted, 58 (6%) were rated
  strong, 462 moderate, 405 weak and 89 unsupported by the paper's own
  evidence.
- **Contribution type predicts quality.** All 14 position papers
  failed. 13 were rejected and one is a hypothesis. Surveys fared
  little better: 4 of 6 that passed review were dropped as
  restatements. Benchmark papers were the most likely to contribute
  (19 of 25 that passed review).
- **Language skew.** SWE-bench appears in 22.3% of coding-agent
  abstracts, Python in 8.4% and Java in 2.9%. Java-specific evidence
  exists (2609.00362, 2607.18057, 2606.24446, 2605.06754, 2607.19682,
  2606.13298, 2608.20167, 2608.30497, 2607.11573) but is thin.
- **Auditor calibration.** Blind auditors were stricter than
  first-pass reviewers. The contribution checker therefore merges the
  audit before capping strength.

## Conflicts between papers

| Question | Side A | Side B | Reading |
| --- | --- | --- | --- |
| Does always-on context help? | Selective loading of standards text: 78.2% (2606.21926) | Always-on: 58.7%, worse than no guidance (same paper) | Load per finding. Keep AGENTS.md short. |
| Is an LLM reviewer reliable? | 96% precision at Ericsson (2609.15877) | Accuracy 0.56 on long-form; manipulable (2606.01629, 2605.26156) | The Ericsson result is author-rated and small. Advisory only. |
| Cheap model or expensive model? | Per-stage routing saves money (2606.22263) | Cheaper models fake verification (2607.25333) | Never route verification-critical steps down. |
| Do specs help? | Acceptance contracts help (2609.22222, 2605.17242, 2605.15846) | More constraints hurt (2605.06445); wording flips security outcomes (2605.29737) | Short executable specs, not long prose. |
| Does mutation score measure test quality? | Kill targets from historical bug classes help (2607.11573) | The top mutation scorer found fewer real bugs (same paper) | Do not gate on generic mutation score. |
| Does feeding errors back help? | Raw javac diagnostics help on compile errors (2609.00362) | Sanitized diagnostics = blind resampling (2609.22222) | Feed raw compiler output. Spend effort on validators. |

## Implications for the Java multi-repo healthcare-content team

These map onto the team's SDD sprint stages. **[E]** marks
recommendations backed by evidence papers. **[H]** marks
recommendations backed only by hypothesis papers. **[J]** marks
engineering judgment that fills a gap in the research.

**Research and Frame (UX, Product)**
- **[E]** Measure outcomes per host and model, not by merge rate.
  Record closure reasons and reviewer touch, and count the invoking
  developer as the author (2605.22534, 2607.07980). Add an owner
  walkthrough to review (2607.26375).
- **[J]** Start agents on narrow, well-specified changes. Treat changes
  to content schemas and templates that ripple downstream as
  high-risk.

**Spec (Design + Engineering)**
- **[E]** A spec is acceptance criteria plus a contract: OpenAPI or
  AsyncAPI for delivery endpoints, and a JSON Schema or Avro for the
  content model.
  - Give each target its own acceptance test (2605.15846).
  - State the constraints and the verification step explicitly
    (2608.09072).
  - State the encoding of defaults and wildcards (2609.22259).
  - Keep layer, ORM and persistence rules in ArchUnit and static
    checks, not in prose (2605.06445).
- **[E]** Put content semantics (field meanings, audience and
  licensing rules, versioning) in a frozen, machine-readable card per
  source. Agents look it up; it is not pasted into AGENTS.md
  (2609.22222, 2609.22259).
- **[E]** Require file:line requirement-to-code links that a
  deterministic check confirms. Agent links are unreliable
  (2606.24834).
- **[J]** For the 4+ repos: write one umbrella spec that owns the
  shared content contract, with per-repo specs that reference it by
  version. Run consumer-driven contract tests in every repo's CI. This
  is the cross-repo gate the research has not studied.
- **[E]** For multi-repo changes, such as a shared library bump or a
  schema rename:
  - have the agent write a JavaParser transformation once and verify
    it in one seed repo, then apply it everywhere;
  - reject regex, raw file and pom edits (2606.24446);
  - resolve replacement APIs from the target artifact, not from model
    memory (2608.30497).

**Gate (QA + Accessibility)**
- **[E]** Hard gates, the same for every host:
  - compile;
  - unit and contract tests;
  - JaCoCo diff coverage on changed lines (2607.18057);
  - direct invocation of the changed method (2608.25939);
  - at least one value or exception assertion per new test
    (2606.18168);
  - no catch-all try/catch around the call under test (2608.20167);
  - containerized behavioural tests for Spring config, DI or
    packaging changes (2605.06754);
  - data-layer tests against the real engine (2605.06445).
- **[E]** Keep acceptance validators that the agent never sees, and
  vary scale, boundaries and order (2608.19799). Re-run every earlier
  unit's acceptance tests at each checkpoint (2608.00267).
- **[E]** Compliance NFRs (learner and patient data privacy, no PHI in
  logs) must be executable checks. Agent self-assessment does not
  count (2606.24834). Write security requirements as exploit tests,
  not principles (2606.25195). Keep deterministic SAST as the gate
  for ingestion endpoints (2608.02001).
- **[E]** LLM review is advisory only, anchored on golden references,
  and is never the merge gate (2606.01629, 2605.26156).
- **[E]** Accessibility repair is gated on zero remaining violations
  with DOM structure preserved, not on "violations reduced"
  (2605.27716).

**Harness configuration (any host)**
- **[E]** Pin host and CLI versions. Rerun a probe of your own Java
  tasks on every upgrade, tracking tokens and turns per task
  (2607.03691). Build the probe with leakage controls: a
  single-commit image, hidden tests and blocked code-host egress
  (2609.08149, 2606.12344). Grade with weighted sub-checks
  (2607.08964).
- **[E]** Enforce permissions and egress in each host's deny/sandbox
  configuration or in hooks. CLAUDE.md prose is not enforcement
  (2608.23550). Audit each gate's precision (2607.07405).
- **[H]** Keep AGENTS.md short and operational: build and test
  commands, module test shortcuts, where contracts live. Lint it in CI
  for stale references (2607.27250, 2606.09090, 2606.15828). This is
  cheap, but it is not proven.
- **[E]** Prefer narrow subagents over role teams (2609.32459). Give
  an orchestrator read-only tools (2609.38345). Hand off through
  artifact files (2608.25457). **[H]** Use at most 2 parallel agents
  per task (2608.23740).
- **[E]** Avoid summarization compaction on long multi-repo tasks. If
  you compress, keep it extractive with a byte-exact read path
  (2608.24188, 2605.11051).
- **[E]** Keep the MCP catalog small and vetted (2606.04769,
  2606.14154). Selection holds at about 15 inlined tools, so tool
  retrieval is unwarranted for a small catalog (2607.15593, Alibaba,
  high COI).

## Limitations of this KB

- **Harvest bias.** Selection used our own topic queries, ranked by
  relevance with 4 papers per topic. This is not a systematic review.
- **Reviewers are LLMs.** Each review and contribution classification
  is one LLM pass. Only 26% of reviews were blind-audited. The gates
  are deterministic, but their inputs are not.
- **Contribution is relative to this team.** "Does not transfer" and
  "restates known" are judged against a Java multi-repo backend team.
  A paper dropped here may matter to a different team.
- **Weight ignores relevance.** Read the pattern matrix alongside the
  contribution ledger.
- **Extraction losses.** HTML-to-text conversion dropped some tables,
  and 1.1% of cited numbers could not be found in the text.
- **Preprints.** Most papers are not peer reviewed. The window closes
  on 2026-10-06, so very recent work is underrepresented.
- **Domain gap.** Almost nothing studies healthcare or education
  content pipelines, or a team's own multi-repo systems.
  Recommendations in those areas are marked [J].
