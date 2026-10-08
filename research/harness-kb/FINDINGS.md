# Findings: agentic harness research, May–early October 2026

Scope: arXiv papers **first submitted** (v1) from 2026-05-01 through
2026-10-07, read for a backend Java team that ingests
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

Every evidence paper has a blind second opinion, merged conservatively.
Pattern labels come from a fixed rule (`etl.py robustness`), not from
judgment. `ADVERSARIAL_REVIEW.md` records what changed when the KB was
stress-tested: single reviews overstated support, and four consensus
labels fell. `dag.md` answers whether DAG-structured workflows would
help.

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
2. **Deterministic sensors are the best-supported investment, but only
   when the sensor is trustworthy. "Tests pass" is weaker than teams
   assume.**
   - After a full blind audit, the execution-verifier loop (P16) is
     *conditional*: 10 supporting evidence papers, 1 contradicting and 14
     mixed. Before the audit it showed 21 supporting. The mixed papers
     name the conditions: tests independent of the implementation,
     coverage of the changed lines, strong oracles, feedback that beats a
     blind redraw. Policy-as-code (P21: 6/0/2) and static analysis in the
     loop (P17: 3/0/1) remain consensus.
   - The same papers show how "green" misleads:
     - existing tests execute only 61.5% of the Java lines agents
       change (2607.18057);
     - 80% of agent test patches carry weak or no oracle (2606.18168);
     - an agentic harness raised pass rate while, on PHP, direct
       invocation of the focal method fell from 98.9% to 27.6%
       (2608.25939);
     - most generated tests that missed a breaking change never loaded
       the changed class. Among those that did, silent null fallbacks
       and catch blocks hid the break (2608.20167);
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
   orchestration pattern. This rests on 5 reviewed papers out of 59
   harvested for the topic, so it is the next topic to deepen. The
   transferable pieces are narrower:
   - agent-authored AST codemods, targeting JavaParser rather than
     Spoon, with regex and pom edits rejected (2606.24446);
   - validating every old→new API mapping against the target artifact
     (2608.30497);
   - typed CodeQL-style queries for cross-service flows in Java
     microservices (2605.15569);
   - grounding each contract-bug alarm in grep-retrieved code
     (2607.00555);
   - static API diffs: 95% of what LLM-written client tests caught on
     dependency bumps was crash-type breakage (missing classes and
     methods), the class japicmp targets. japicmp itself was not
     measured (2608.20167).
6. **Healthcare and education content is still a research gap.**
   - T56 has 1 evidence paper and T57 has none.
   - Reviewers agreed with 91–94% of an agent's NFR assessments, which
     scored only 0.38 F1 against experts (2606.24834). The same paper
     shows agent requirement-to-code links reach about 0.2 F1 on Java.
   - Agent accessibility repair fully fixed fewer than 26% of files
     and altered the structure of about 30% (2605.27716).
7. **DAG-structured workflows: keep the outer graph fixed and
   deterministic, and let each node run a bounded agent loop.**
   - **Static workflow graphs (P36) are conditional (2/0/8).** They won
     where the stages carried domain signals: an incident-repair
     pipeline beat an open loop on one model at 4% of the tokens
     (2608.17018). They fell behind on multi-file work (28.9 vs 46.6,
     2605.16352).
   - **Model-drawn task DAGs (P37) are only leaning (2/0/2).** An
     upfront DAG tied ReAct (43.7 vs 43.0); growing it from evaluated
     results scored 55.9 (2609.39154). Model-drawn edges were
     unreliable (edge F1 0.27–0.71, 2608.00267).
   - **Graph frameworks add no speed:** an auto-parallelizing compiler
     ran the same workflows 2.0–3.2× faster than seven frameworks
     (2605.18697).
   - **Isolation is the edge that matters most:** tests generated after
     seeing the code lost 8–18 points of fault detection (2607.05139).
   - Details are in `dag.md`.
8. **The completed workflow adds a frame and a read-only question
   pass in front of the spec. It does not add an agent that writes
   the spec.**
   - Pre-spec discovery (P38) is leaning, on one paper: two cited
     repository answers before the edit raised Pass@1 by 3.8 and 4.4
     points, and a root-cause proposal did not (2607.11111). That
     label is none on Java and when SWE-bench papers are removed.
   - Clarifying questions (P40) are unresolved. Empty slots should
     force one question to a person (2605.09698, 2607.02294). More
     questions did not help. Runnable acceptance fixtures did: 37.4%
     to 61.8% (2607.21217).
   - Domain cards (P39) are conditional. Codebase exploration (P43)
     is consensus and falls to unresolved without SWE-bench.
     Explanations (P41) are contested. Verified trace links (P42)
     have no evidence paper.
   - Details are in `discovery.md`.

## Method

| Stage | Result |
| --- | --- |
| Research topics | 69 topics in 11 clusters (`taxonomy.json`), each with phrase queries across 11 arXiv categories. T59–T61 were added for the DAG question. T62–T69 were added for discovery, onboarding, clarification, comprehension and traceability |
| Harvest | 7,235 unique papers in the window; 4,940 passed the relevance gate |
| Selection | 427 candidates: 278 from the earlier rounds, then 149 for T62–T69 (ranked by relevance, with a code-term filter on the second pick). See `discovery.md` |
| Date audit | v1 `published` date inside the window, rechecked live against arXiv for all 427 (`etl.py recheck`); withdrawn or author-discarded papers rejected (see below) |
| Full text | Read from arXiv HTML, with a pdftotext fallback |
| Pre-review signals | Vendor affiliations, artifact URLs, and limitations/ethics/acknowledgment sections, extracted deterministically |
| Adversarial review | Each paper reviewed against `REVIEW_RUBRIC.md`: 5 scores (0–5), bias codes, COI severity, claim strength, per-pattern stance |
| Blind audit | 223 papers, including every one of the 152 evidence papers. Each was re-reviewed before reading the first review. Merged conservatively: lowest score, strictest verdict, weakest claim strength and the auditor's stance changes win |
| Hallucination check | 4,815 numbers cited in the first 240 reviews matched against the paper text; 53 (1.1%) not found, mostly derived values. The script was not committed and was not rerun for the 38 DAG-batch reviews. A separate agent checked the numbers in this file, `dag.md` and `ADVERSARIAL_REVIEW.md` against the texts (`ADVERSARIAL_REVIEW.md` §9) |
| Review gate | Deterministic code (`etl.py admission`), not LLM judgment |
| Contribution gate | Each review-passing paper classified against `CONTRIBUTION_RUBRIC.md`, then gated by code (`etl.py contribution_gate`). Strength is capped at the paper's strongest audited claim. A paper with no assessment loads as `unassessed`, not evidence |
| Pattern labels | Fixed rule (`pattern_label`), stress-tested on subsets in `kb_robustness.md` |

Outcome for the 427 reviews:

| Status | Papers | Mean rigor | Meaning |
| --- | --- | --- | --- |
| Evidence (caveated) | 152 | 2.84 | Passed both gates |
| Hypothesis | 65 | 2.32 | A transferable idea, but on weak evidence, or the paper is self-declared preliminary |
| No contribution | 43 | 2.44 | Restates known practice, duplicates a stronger paper, or does not transfer |
| Rejected | 167 | 1.56 | Failed review, including off-topic keyword matches; 1 withdrawn and 1 whose authors discarded the experiments |

No paper cleared every check cleanly, and the best scored rigor 4 of
5. Rigor alone does not separate volume papers from useful ones:
dropped papers averaged rigor 2.44, close to the hypotheses. Most were
competent work that told this team nothing new. Treat everything below
as directional evidence, not settled science.

Evidence weight per paper:
`(rigor/5) × (0.6 + 0.4·repro/5) × (1 − 0.12·coi_risk)`, multiplied by
0.6 if caveated and set to 0 for every non-evidence status. The
highest weight in the KB is 0.48.

### Date audit

The window applies to the **first** submission. A paper first posted
before May 2026 and only revised inside the window does not qualify.
`admission` checks the v1 `published` date.

| Check | Result |
| --- | --- |
| v1 dates of the 427 reviewed papers | 2026-05-01 … 2026-10-07 |
| v1 before 2026-05-01 | 0 |
| Revised on arXiv since we reviewed them (live recheck of all 427, 2026-10-08) | 0 |
| Withdrawn or discarded | 2: 2606.14066, a lock citation, and 2608.28421, whose authors discarded the experiments. Both rejected |
| Evidence papers first posted after 2026-09-30 | 5 (2610.01769, 2610.02932, 2610.02952, 2610.04940, 2610.07851). Dropping them changes one label (P28). P38–P43 do not change |
| Self-declared work in progress | 8 flagged `self_declared_incomplete`; capped at hypothesis |

### Contribution audit

Of the 260 papers that passed review, 108 (42%) added nothing the team
can use on adequate evidence. Quantity-over-quality flags:

| Flag | Papers | What it catches |
| --- | --- | --- |
| numbers_without_mechanism | 23 | Gains reported without the ablation that says why |
| position_without_evidence | 17 | Argument only |
| system_description_only | 13 | "We built X" with no outcome measure |
| survey_restatement | 11 | Reorganises known advice |
| self_declared_incomplete | 11 | Authors call it preliminary or WIP |
| leaderboard_only | 11 | Rankings with no transferable lesson |
| renamed_known_idea | 7 | A new name for established practice |

Qualifying contributions from the 152 evidence papers: 64 nuances,
53 test practices, 49 heuristics, 23 constraints, 21 anti-patterns
and 18 design patterns. Each one is listed in `kb_contributions.md`.

## Where each pattern lands

Counts are evidence papers only, after the audit merge, written as
supports / contradicts / mixed. Labels come from the fixed rule in
`kb_robustness.md`. That file also shows which labels hold on the Java,
non-SWE-bench, no-COI and pre-October subsets, and without each
pattern's top paper.

### Consensus: build these

| Pattern | S / C / M | What the evidence actually says |
| --- | --- | --- |
| P21 Policy-as-code guardrails | 6 / 0 / 2 | Declared forbidden operations stopped mutating SQL (2609.22259). Blocking egress closed leakage channels (2609.08149). Put a deterministic predicate in front of write tools, and audit each gate's precision by minus-one removal (2607.07405). Route by enrolled IDs, never display names (2609.27624). |
| P34 Structured acceptance criteria | 5 / 0 / 4 | A fully specified output contract (2609.22222). Acceptance-test-first repair, keeping the best checkpoint (2605.17242). Under-specified defaults (2609.08149, 2609.22259). A requirement-to-component map (2608.19854). |
| P13 Planner-executor | 5 / 0 / 5 | Plan verification together with implementation (2608.09277). A plan → develop → independent-test loop beat plain continuation at fewer tokens (2609.01481). Hand off through artifact files, not transcripts (2608.25457). A hard stage break with a structured handoff beat a prompt-described pipeline (2606.22263). Falls to conditional without its top paper (2608.19854). |
| P24 Token and cost budgets | 4 / 0 / 2 | An explicit cumulative budget capped worst-case overspend (2610.02932). Billed cost cross-checked against provider dashboards (2606.22263). On one model, a selector plus intermediate form used 0.55× the tokens at equal or better validity (2608.30250). |
| P17 Static analysis in the loop | 3 / 0 / 1 | Rule-based compile repair beat LLM repair loops for Java test generation (2607.19682, Huawei, medium COI). Static-analysis output drives the loop on cross-service Java flows (2605.15569). A deterministic checker as the repair oracle (2606.21926). Thin: falls to leaning on the Java and no-SWE-bench subsets. |
| P30 Observability and audit | 3 / 0 / 2 | Functional CI passed while token cost rose 52–131% (2607.03691). Trajectory audits exposed reward hacking (2609.08149). Event streams show whether a declared workflow actually happened (2609.38345). |
| P43 Codebase question answering / exploration | 5 / 0 / 4 | Two cited repository answers before the edit raised Pass@1 by 3.8 and 4.4 points; a root-cause proposal did not (2607.11111). Exploration beat one-shot embedding QA, including 59–63 vs 47–49 on a 30-question Java subset (2608.24221). Line recall stayed 0.05–0.19 while file hit looked fine (2606.07297). Falls to unresolved on Java-evaluated papers and without SWE-bench. See `discovery.md`. |
| P15 TDD with agents | 3 / 1 / 2 | Tests written first from the spec, or by an author isolated from the implementation, help (2605.17242, 2607.05139). Runnable tests available before implementation added 24.4 points in one intervention (2607.21217, single model). Agent-authored tests did not help, and self-scores saturated (2607.24300). Flips to contested without SWE-bench and without its top paper. |
| P20 OS sandboxing | 3 / 0 / 1 | Prompt prohibitions left 20–36% of runs looking up source (2605.03546). A networked eval fetched the upstream answer in 26 of 85 runs (2609.39909). Unresolved on Java, and none when SWE-bench papers are removed. |

P25 (RL fine-tuning, 4/0/1) and P32 (field evaluation, 5/0/1) also reach
the bar. P25 belongs to the agent host (Job A). P32 is a study method,
not a harness choice.

### Conditional: works where measured, if its conditions hold

| Pattern | S / C / M | Conditions the mixed papers name |
| --- | --- | --- |
| P16 Execution verifier loop | 10 / 1 / 14 | Only as good as the verifier. The tests must not come from the code they check: tests written after seeing the code lost 8–18 points (2607.05139), and same-agent tests agree on wrong behaviour (2608.16742). They must execute the changed lines (2607.18057) and carry a value oracle (2606.18168). Feedback must beat a blind redraw at the same budget (2609.22222). JUnit 4 test feedback was no better than "code is wrong" in Java, while raw javac diagnostics helped (2609.00362). Accept a defect claim only with a reproducing failing test (2606.22263). Cap repair retries at about 3 (2609.03086). |
| P05 Lexical/deterministic retrieval | 3 / 0 / 7 | Deterministic AST/PSI or CodeQL retrieval beat model inference of context (2607.19682, 2605.15569). Lexical grounding cut contract-alarm false positives from 60.5% to 13.9% (2607.00555). Alone, lexical search is the weakest retriever; it helps in fusion or anchored to structure (2605.16352). |
| P02 Skills loaded on demand | 2 / 0 / 7 | Selective loading of standards text beat always-on (2606.21926). Procedural skills recovered pass rate at lower cost (2607.16617). |
| P36 Static workflow graph | 2 / 0 / 8 | Wins when stages carry domain signals or deterministic rules (2608.17018, 2608.19854). Cheap but behind open loops on multi-file work (2605.16352); more side effects (2606.21926). See `dag.md`. |
| P39 Machine-readable domain context | 4 / 0 / 6 | A fetched YAML contract beat the same knowledge pasted as a manual (2609.22259). A fault taxonomy plus symptom-to-cause rules gained 8.6–21.6 points (2607.13548). Security-guideline records and issue-specific cards each won an ablation (2608.25457, 2609.31176). Unresolved on the Java subset. See `discovery.md`. |

### Contested: use narrowly and measure

| Pattern | S / C / M | Why it is contested |
| --- | --- | --- |
| P18 LLM-as-judge or AI reviewer | 1 / 2 / 12 | Mean judge accuracy is 0.56 on long-form outputs (2606.01629). Style edits raise judge scores (2605.26156). Advisory only. |
| P41 Comprehension and skill safeguards | 0 / 1 / 3 | Explanations did not improve accuracy at judging assertions, and underspecified ones raised confidence (2607.08885). Agent users recall less of their own code (2607.26375). See `discovery.md`. |
| P08 Context compaction | 0 / 2 / 9 | Learned compression hurt resolution (2605.11051). Native compaction lost an exact 256-entry contract (2607.17937). If you compress, keep it extractive with a byte-exact read path (2608.24188). |
| P11 Multi-agent role teams | 0 / 1 / 5 | Generic role teams hurt (2609.32459). A model-directed team realized its declared organization in only 47.2% of runs (2609.38345). |
| P06 Embedding RAG over code | 2 / 1 / 4 | Code embedding indexes are poisonable (2608.26031). Dense eager candidates helped one repair setup (2607.25431). |
| P07 Code/knowledge graph context | 3 / 1 / 1 | Graph context helps injected into a lexical loop (2605.16352, 2609.16936). A temporal knowledge graph fragmented specification facts (2607.26072). |
| P09 Persistent memory | 0 / 1 / 5 | Memory can carry insecure preferences across sessions (2607.17619). Keep durable preferences in committed files. |
| P22 Prompt-injection defenses | 1 / 1 / 3 | Tree-sitter sanitization cut injection about 3× (2606.19235). Prompt-level warnings were bypassed on every pair tested (2605.11229). Defenses must sit outside the model context. |
| P26 Self-improving harness | 1 / 1 / 3 | Agents tamper with their own harness (2609.00069). Evolved workflows beat a hand-written seed on held-out sets (2607.16387). Require graded predictions for harness changes (2609.01861, hypothesis only). |
| P33 CLI-first / code-as-action | 1 / 1 / 4 | Adding native read/write/edit tools beat a bash-only loop by 3.5–4.6 pp (2609.32459). |

### Unsupported, unresolved or unstudied: do not budget for these as quality levers

| Pattern | S / C / M | Status |
| --- | --- | --- |
| P37 Model-generated task DAG | 2 / 0 / 2 | Leaning. Only when grown from evaluated results (2609.39154) or checked by deterministic rules (2608.19854). See `dag.md`. |
| P38 Pre-spec knowledge discovery | 1 / 0 / 1 | Leaning, and only for a read-only question pass before a fix (2607.11111). No evidence paper supports an agent that explores and then writes the spec. None on Java and when SWE-bench papers are removed. See `discovery.md`. |
| P40 Clarifying questions | 0 / 0 / 4 | Unresolved. Asking wins against an oracle and is miscalibrated (2605.09698). More questions did not raise pass rate (2607.21217). Force a question when a required slot is empty (2607.02294). |
| P42 Verified requirement-to-code links | 0 / 0 / 0 | No evidence paper. TraceDev (2607.18886) is a hypothesis: its success rate counts tests an unvalidated judge passed first. |
| P35 Formal and independent checkers | 2 / 0 / 2 | Leaning (was consensus before the full audit). TLA+ model checking found real bugs (2607.25333). Fuzz agent-inferred contracts (2605.27531). |
| P12 Task-specific subagents | 1 / 0 / 5 | Unresolved (was consensus). A persistent lookup-only search subagent (2605.27787). Pre-inject retrieved files only when retriever precision is high (2608.05886). |
| P14 Spec-driven development as a methodology | 1 / 0 / 2 | Unresolved. The specific spec practices under P34 carry the evidence; SDD adoption has none. |
| P27 Cross-repo coordination | 0 / 0 / 3 | Unresolved on 5 reviewed of 59 harvested papers. |
| P28 Deterministic codemods | 1 / 0 / 2 | Unresolved. One paper (2606.24446), but it is Java-specific and direct. |
| P10 Single-agent loop, P19 human approval gates, P23 model routing, P31 benchmark evaluation, P04 MCP | 0–1 / 0 / 2–4 | Unresolved: mixed papers outnumber supporting ones. |
| P29 parallel worktrees | 1 / 0 / 1 | Leaning, one paper. |
| P01 Instruction files, P03 small tool catalog | 0 / 0 / 0 | No evidence paper. P03's only support (2607.15593) was rejected in the full audit (rigor 2, high COI). |

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
| Per-node structured traces with contracts localize workflow faults (59.8% → 84.4%) | 2607.02882 | Overall lead depends on parts learned from the test data |
| Route handoffs in code; declared handoff edges went unwitnessed by generated tests (10/41 delegations) | 2605.26521 | Restricted-edge counts inflated by construction |
| Hard evidence gates between stages, plus a bounded repair loop | 2609.00050 | Gate effect not significant (0 vs 4 bad transitions of 420); one cloud, greenfield |
| Model-generated atomic task graph beats ReAct | 2607.01942 | 7B models on text games; extra calls not counted |
| Require graded predictions before accepting a harness change | 2609.01861 | Gains vanish on the unscreened split and after a target-model swap |

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

Bias codes across the 427 reviewed papers:

| Bias | Papers | Share |
| --- | --- | --- |
| Metric does not measure the claim | 216 | 51% |
| No variance reported | 205 | 48% |
| Small sample | 200 | 47% |
| Self-evaluation (authors' own system and metric) | 192 | 45% |
| Closed artifacts | 162 | 38% |
| Hype language | 144 | 34% |
| Single model | 115 | 27% |
| Strawman baseline | 114 | 27% |
| Contamination risk | 106 | 25% |
| Toy tasks | 92 | 22% |

- **Conflicts of interest.**
  - 18 papers had a high COI: 15 rejected, 1 hypothesis, 2 evidence.
  - 34 had a medium COI: 15 rejected, 9 hypothesis or no contribution,
    10 evidence.
  - High- and medium-COI papers averaged rigor of about 1.9, against
    about 2.3 for low or no COI.
- **Claim strength.** Of 1,872 claims extracted, 79 (4%) were rated
  strong, 689 moderate, 868 weak and 236 unsupported by the paper's own
  evidence.
- **Contribution type predicts quality.** Of 16 position papers, 15
  were rejected and one is a hypothesis. Surveys fared little better: 4
  of 6 that passed review were dropped. Of the larger types, benchmark
  papers were the most likely to contribute (19 of 25 that passed
  review).
- **Language skew.** SWE-bench appears in 21.4% of coding-agent
  abstracts, Python in 8.2% and Java in 2.7% (`landscape.md`). 25 of
  the 152 evidence papers mention Java at least 5 times. On that
  subset, P43 and P38 lose their labels (`kb_robustness.md`).
- **Auditor calibration.** Blind auditors changed 59% of first-pass
  `supports` stances (157 of 266): 63 to neutral, 61 to mixed and 33 to
  introduces. The contribution checker merges the audit before capping
  strength.

## Conflicts between papers

| Question | Side A | Side B | Reading |
| --- | --- | --- | --- |
| Does always-on context help? | Selective loading of standards text: 78.2% (2606.21926) | Always-on: 58.7%, worse than no guidance (same paper) | Load per finding. Keep AGENTS.md short. |
| Is an LLM reviewer reliable? | 96% precision at Ericsson (2609.15877) | Accuracy 0.56 on long-form; manipulable (2606.01629, 2605.26156) | The Ericsson result is author-rated and small. Advisory only. |
| Cheap model or expensive model? | Per-stage routing saves money (2606.22263) | Cheaper models fake verification (2607.25333) | Never route verification-critical steps down. |
| Do specs help? | Acceptance contracts help (2609.22222, 2605.17242, 2605.15846) | More constraints hurt (2605.06445); wording flips security outcomes (2605.29737) | Short executable specs, not long prose. |
| Does mutation score measure test quality? | Kill targets from historical bug classes help (2607.11573) | The top mutation scorer found fewer real bugs (same paper) | Do not gate on generic mutation score. |
| Does feeding errors back help? | Raw javac diagnostics help on compile errors (2609.00362) | Sanitized diagnostics = blind resampling (2609.22222) | Feed raw compiler output. Spend effort on validators. |
| Fixed workflow or open agent loop? | Fixed incident-repair pipeline beat an open loop at 4% of the tokens (2608.17018); fixed repair solved more accessibility bugs (2606.21926) | Agentless-style pipeline far behind on multi-file localization (2605.16352); more side effects (2606.21926) | Fix the outer stages and gates; leave the code change to a bounded loop (`dag.md`). |

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
  - no catch-all try/catch or null fallback hiding the call under
    test (2608.20167);
  - containerized behavioural tests for Spring config, DI or
    packaging changes (2605.06754);
  - data-layer tests against the real engine (2605.06445).
- **[E]** Keep acceptance validators that the agent never sees, and
  vary scale, boundaries and order (2608.19799). Re-run every earlier
  unit's acceptance tests at each checkpoint (2608.00267).
- **[E]** Generate tests from the spec, in a context that cannot see
  the implementation or the coding agent's conversation. Tests written
  right after the code lost 8–18 points of fault detection on 5 of 5
  models (2607.05139).
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
- **[E]** Avoid generic role teams (2609.32459). Script handoffs in
  code if they must happen: a model-directed team realized its declared
  organization in 47.2% of runs (2609.38345). Hand off through artifact
  files (2608.25457). Subagents for exploration (P12) are unresolved
  after the full audit (1 supporting, 5 mixed), so use them for context
  isolation, not as a quality lever. **[H]** Use at most 2 parallel
  agents per task (2608.23740).
- **[E]** Keep the workflow graph fixed, deterministic and in CI: SDD
  stages, gates, provider-first merge order. Each node runs a bounded
  agent loop, and edges are files such as the spec, the lock and
  reports. Validate agent output before any shell or git step reads it
  (2605.07135). Don't adopt a graph runtime for coding: no speed gain
  (2605.18697), and no production harness uses one (2609.00006). See
  `dag.md`.
- **[E]** Avoid summarization compaction on long multi-repo tasks. If
  you compress, keep it extractive with a byte-exact read path
  (2608.24188, 2605.11051).
- **[E]** Vet the MCP catalog: about 10% of tool descriptions
  misrepresent the code (2606.04769), and scanners miss split-intent
  skill attacks (2606.14154). **[J]** Keep it small. The ~10–15 tool cap
  in `AGENTS.md` is policy. The paper that measured selection at about
  15 tools (2607.15593) was rejected in the full audit.

## Limitations of this KB

- **Harvest bias.** Selection used our own topic queries, ranked by
  relevance with 4 papers per topic (10 for T59–T61). This is not a
  systematic review. A topic not queried is invisible: DAG workflows
  were until T59–T61 were added, and P27 has only 5 reviewed papers of
  59 harvested.
- **Reviewers are LLMs.** Each review and contribution classification
  is one LLM pass. All 152 evidence papers have a blind audit, but
  reviewer and auditor are the same model family, so shared blind spots
  remain. Agreement is lowest on relevance (66 of 138 exact). The gates
  are deterministic, but their inputs are not.
- **Vote counting.** Pattern labels count papers and weight them by an
  ad hoc formula. This is not a meta-analysis. `kb_robustness.md` shows
  which labels rest on one paper or one subset.
- **Contribution is relative to this team.** "Does not transfer" and
  "restates known" are judged against a Java multi-repo backend team.
  A paper dropped here may matter to a different team.
- **Weight ignores relevance.** Read the pattern matrix alongside the
  contribution ledger.
- **Extraction losses.** HTML-to-text conversion dropped some tables,
  and 1.1% of cited numbers could not be found in the text.
- **Preprints.** Most papers are not peer reviewed. The window closes
  on 2026-10-08, so very recent work is underrepresented. The discovery
  round is written up in `discovery.md`.
- **Domain gap.** Almost nothing studies healthcare or education
  content pipelines, or a team's own multi-repo systems.
  Recommendations in those areas are marked [J].
