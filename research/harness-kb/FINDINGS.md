# Findings: agentic harness research, May–early October 2026

Scope: arXiv submissions dated 2026-05-01 through 2026-10-06, read for
a backend Java team that ingests healthcare-education content across
at least four repositories and delivers it to front-end applications.
The team is rolling out spec-driven development (SDD) through a
Research → Frame → Spec → Gate sprint.

All numbers below come from `kb.sqlite`. Regenerate it with
`python3 etl.py load && python3 etl.py report`. The supporting tables
are in `kb_tables.md`, the per-pattern evidence is in `kb_evidence.md`,
and the abstract-level trend counts are in `landscape.md`.

## Bottom line

1. **The harness matters about as much as the model, and almost
   nobody controls for it.** With the model held fixed, changing the
   harness moved resolve rate by up to about 24 pp and cost by
   several-fold (2606.12344). In another study it moved tokens per
   solved task by up to about 40x (2607.22585). Thirty-five releases
   of one CLI produced 52–131% token swings that functional CI did not
   catch (2607.03691). Treat each host+version+model combination as
   the unit you evaluate. Pin versions, and run your own regression
   suite of Java tasks.
2. **Deterministic sensors are the best-supported investment, but
   "tests pass" is a weaker signal than teams assume.**
   - The execution-verifier loop (P16) has by far the most support:
     30 supporting papers against 2 contradicting (weighted 7.32 vs
     0.42).
   - The same papers show what goes wrong:
     - existing tests cover only 61.5% of the Java lines agents
       change, and 86% of catch blocks go unexecuted (2607.18057);
     - agent-written tests mostly lack real oracles (2606.18168);
     - public tests pass while hidden tests fail (2608.19799);
     - compiling is not the same as preserving behaviour: the best
       agents reach about 15% on enterprise Java framework migration
       (2605.06754).
   - What to build: diff coverage, assertion-strength checks and
     behavioural or contract tests, not only "mvn test is green".
3. **There is no evidence that spec-driven development (P14) works as
   a methodology, but structured acceptance criteria (P34) are well
   supported.**
   - P14 has 2 supporting papers, 7 mixed and 12 that only introduce
     an approach. Every SDD-framework paper we found was a position
     paper, a corpus, or vendor-adjacent.
   - Precise output contracts and acceptance tests do help (P34: 7
     supporting, 0 contradicting). One study saw a 23.4 pp swing from a
     fully specified output contract (2609.22222).
   - Piling non-functional constraints into a spec makes backend
     agents worse ("constraint decay", 2605.06445).
   - Write specs as short, testable contracts and enforce the
     structural rules with deterministic tools, not prose.
4. **Instruction files (AGENTS.md/CLAUDE.md, P01) do not raise
   correctness, and they cannot enforce policy.**
   - The one controlled ablation found no detectable effect on
     correctness (2607.27250; it is underpowered and covers Python
     only).
   - Only about 4.4% of security rules written in CLAUDE.md have a
     built-in control that would enforce them (2608.23550).
   - 23% of repos have instruction files that reference stale code
     (2606.09090).
   - Keep these files short and operational, and enforce policy
     through permissions and hooks.
5. **Cross-repo coordination (P27), which is your core problem, is
   essentially unstudied.** No paper supports a cross-repo
   orchestration pattern. Auditors downgraded every apparent
   "support" because the evidence was about third-party dependency
   upgrades, not a team's own interlocking repos. The closest usable
   result is agent-authored AST codemods: write the change once,
   verify it, and apply it to every repo (2606.24446).
6. **Healthcare and education content is a gap in the research.**
   - The healthcare-compliance topic (T56) admitted 2 papers, and
     educational content (T57) admitted none.
   - The one relevant HIPAA study found that humans agreed with an
     agent's NFR assessments 91–94% of the time, while those
     assessments scored only 0.38 F1 against experts (2606.24834).
   - An agent self-assessment plus a human "looks right" is not
     compliance evidence.

## Method

| Stage | Result |
| --- | --- |
| Research topics | 58 topics in 11 clusters (`taxonomy.json`), each with phrase queries across 11 arXiv categories |
| Harvest | 5,585 unique papers in the window; 3,989 passed the relevance gate |
| Selection | 228 candidates (4 per topic, ranked by relevance; T26/T57 had only 2) |
| Full text | All 228 read from arXiv HTML, with a pdftotext fallback |
| Pre-review signals | Vendor affiliations in the front matter, artifact URLs, and limitations/ethics/acknowledgment sections, extracted deterministically |
| Adversarial review | Each paper reviewed against `REVIEW_RUBRIC.md`: 5 scores (0–5), 25 bias codes, COI severity, claim strength, per-pattern stance |
| Blind audit | 59 papers (26%) independently re-reviewed without seeing the first review: 5 agreed, 50 minor and 4 major disagreements. Merged conservatively: lowest score and strictest verdict win |
| Hallucination check | 4,815 numbers cited by reviewers were matched against the paper text; 53 (1.1%) were not found, mostly derived values |
| Admission gate | Deterministic code (`etl.py admission`), not LLM judgment |

Gate outcome: 0 clean admits, 154 admitted with caveats, 74 rejected.
Of the rejections, 39 were off-topic (the query harvest picked them
up) and 35 were rejected on quality. No paper cleared every check.
The single best paper scored rigor 4 of 5. Treat everything below as
directional evidence, not settled science.

Evidence weight per paper:
`(rigor/5) × (0.6 + 0.4·repro/5) × (1 − 0.12·coi_risk)`, multiplied by
0.6 if caveated and set to 0 if rejected. The highest weight in the
KB is 0.48.

## Where each pattern lands

These counts come from the pattern evidence matrix after the audit
merge. "Supp" and "Contra" are numbers of non-rejected papers.

### Consensus: build these

| Pattern | Supp / Contra | What the evidence actually says |
| --- | --- | --- |
| P16 Execution verifier loop | 30 / 2 | Strongest pattern overall. For Java, javac feedback helps on compile errors. Raw JUnit 4 output is barely better than "tests failed" for logic bugs (2609.00362), so make failure output informative: expected/actual values, trimmed stack traces, the failing test source. mvn compile/test loops fixed breaking dependency updates (2606.24446). |
| P17 Static analysis in the loop | 7 / 1 | AST/PSI-derived context and rule-based compile repair beat LLM repair loops on proprietary Java (2607.19682, Huawei, medium COI). |
| P05 Lexical/deterministic retrieval | 10 / 0 | Grep/AST retrieval is reliable. An LSP is not a default win: grep was better for localization, and the LSP only helped finding references among noisy, colliding names (2608.13568). Java's `getId`/`*Mapper` boilerplate is exactly that noisy case, so test an LSP on reference-finding only. |
| P21 Policy-as-code guardrails | 7 / 2 | Declared forbidden operations stopped all mutating SQL (2609.22259). Blocking network egress closed benchmark leakage channels (2609.08149). Classifier guardrails get bypassed (2609.09798): enforce deterministically. |
| P24 Token and cost budgets | 12 / 0 | Uniform turn and time caps are needed to compare hosts at all (2607.22585). |
| P34 Structured acceptance criteria | 7 / 0 | Fully specified output contracts (2609.22222). Acceptance-test-first helps capable models (2605.17242). Under-specified constants and defaults caused 21 of 102 refined benchmark failures (2609.08149). |
| P30 Observability and audit | 9 / 0 | Mostly introduces tooling. Agent PR merge rate is a confounded KPI: 15.4% of merges needed reviewer fixes (2605.22534). Log CI results, reviewer commits and closure reasons. |
| P12 Task-specific subagents | 3 / 0 | Narrow subagents with restricted tools gave the largest single ablation gain, about +5.9 pp (2609.32459). A persistent read-only "librarian" search subagent cut energy use (2605.27787). |

### Contested: use narrowly and measure

| Pattern | Supp / Contra | Why it is contested |
| --- | --- | --- |
| P18 LLM-as-judge or AI reviewer | 5 / 5 (23 mixed) | Mean judge accuracy is 0.56 on long-form outputs, with failures on clinical content (2606.01629). Style-manipulation attacks flip verdicts (2605.26156). Ericsson's per-dimension review subagents reached 96% precision as rated by the commits' own authors, on 7 commits (2609.15877). Use an LLM judge as an advisory signal anchored on reference examples, never as the gate. |
| P08 Context compaction | 7 / 3 | Every compression method tested lowered pass rate (2609.08318). Compaction drops exact obligations (2607.17937). Prefix stability matters for KV-cache cost (2609.33762). Prefer subagent isolation and files on disk over summarization. |
| P11 Multi-agent role teams | 1 / 2 (9 mixed) | Generic architect/coder/tester role agents hurt results (2609.32459). Quality peaks at 2 parallel agents (2608.23740). Declared "collaboration" often doesn't happen. 13 papers only introduce frameworks. |
| P06 Embedding RAG over code | 4 / 3 | Mentions in abstracts fall from 6.1% (May) to 2.5% (Oct). Structural context beats embedding chunks for cross-file Java (2609.12464, Google Cloud, medium COI, weak). |
| P02 Skills and progressive disclosure | 4 / 1 (9 mixed) | Reuse is limited (138K SKILL.md files, 2608.08453). Skill files have smells (2607.01456) and supply-chain risk (2606.14154), and they lose force over long trajectories. Per-task skill bundles help migration a little (2605.06754). |
| P23 Model routing | 7 / 1 | Per-stage routing between Haiku and Sonnet works (2606.22263), but cheaper models cost more per fixed bug (2607.25333). Routing is the host's decision, not the router's (see AGENTS.md). |
| P15 TDD with agents | 2 / 0 (5 mixed) | The main failure mode is self-consistent wrong tests. Tests must come from the spec or a human, not from the agent that writes the code. |
| P26 Self-improving harness | 2 / 3 | Self-authored verification is unreliable (2607.24300). Agents tamper with their own harness (2609.00069). |
| P04 MCP | 2 / 1 | About 10% of MCP tool descriptions misrepresent what the code does (2606.04769), plus runtime faults (2606.05339) and privacy leaks (2606.21338). Keep the catalog small and vetted. |

### Unsupported or unstudied: do not budget for these as quality levers

| Pattern | Supp / Contra | Status |
| --- | --- | --- |
| P01 Instruction files | 0 / 0 (3 mixed) | No correctness effect found. Useful as operational hints only. |
| P14 Spec-driven development as a methodology | 2 / 0 (12 introduce) | Only SpecMine (2608.25202) measures adoption: 470,795 spec files in 73,030 repos, with no outcome data. The Google SDD test-generation paper (2608.17177, medium COI) derives its specs from existing code and shows modest gains only at k≥4 attempts, for about 38% more tokens. Three SDD framework papers were rejected for having no evaluation (2609.00252, 2609.24348, 2608.16618). |
| P27 Cross-repo coordination and contracts | 0 / 0 | No direct evidence. Cross-repo appears in 0.9% of coding-agent abstracts. |
| P29 Parallel agents in worktrees | 3 / 0 | Thin. The most concrete design paper (2606.27416) was rejected as an experience report. |
| P22 Prompt-injection defenses | 2 / 0 | Weighted support is only 0.16. Attacks far outnumber evaluated defenses. |
| P28 Deterministic codemods | 3 / 0 | Promising for Java (2606.24446) but only 3 papers, with about 40% end-to-end success. |

## Theories and frames that recur

- **Harness as a hidden variable.** Benchmark results confound the
  model with the scaffold (2606.12344, 2607.22585, 2607.03691,
  2609.32459). This is the most consistent theme in the corpus.
- **Guides vs. sensors.** Every guide the evidence covers is weak:
  instruction files, skills, spec prose and compaction summaries.
  Deterministic sensors are strong: compilers, tests, static rules,
  policy. The asymmetry favours spending on sensors.
- **Constraint decay.** Each added prose constraint raises the failure
  rate, and failures concentrate in the data layer (2605.06445). This
  matters for ingestion code, which is mostly data-layer code.
- **Comprehension debt.** Agent users ship faster but understand their
  own code less (2607.26375). In mature Java repos, architectural
  smell counts stayed flat while LOC grew 12.8% (2606.13298, the
  top-weighted paper): the immediate risk is volume, not decay.
- **Benchmark leakage.** Future-commit leaks in SWE-bench-Multilingual
  images (2606.12344). Git-history and network leakage inflated one
  model from 57% to 79% (2609.08149). Any internal evaluation built
  from your repo history must strip future objects and block egress.

## Biases and conflicts of interest in the literature

Bias codes recorded across the 228 reviewed papers:

| Bias | Papers | Share |
| --- | --- | --- |
| No variance reported | 114 | 50% |
| Small sample | 104 | 46% |
| Self-evaluation (authors' own system and metric) | 101 | 44% |
| Metric does not measure the claim | 99 | 43% |
| Closed artifacts | 74 | 32% |
| Hype language | 63 | 28% |
| Single model | 56 | 25% |
| Contamination risk | 55 | 24% |
| Strawman baseline | 52 | 23% |
| Unvalidated LLM judge | 52 | 23% |
| Python only | 38 | 17% |

- **Conflicts of interest.**
  - 9 papers had a high COI: 7 rejected, mean rigor 1.67.
  - 15 had a medium COI: 6 rejected, mean rigor 1.87.
  - Papers with low or no COI averaged rigor 2.37–2.38.
  - Vendor-authored papers were most common in the observability
    (22%), worktree (27%) and codemod (25%) patterns. Those are
    exactly the areas where products are being sold.
- **Claim strength.** Of the 958 claims extracted, 55 (6%) were rated
  strong, 440 moderate, 379 weak and 84 unsupported by the paper's own
  evidence.
- **Contribution type predicts quality.** Position papers averaged
  rigor 0.93, and 13 of 14 were rejected. Benchmark papers were the
  most rigorous (2.74), followed by empirical papers (2.60).
- **Language skew.** SWE-bench appears in 22.3% of coding-agent
  abstracts, Python in 8.4% and Java in 2.9%. Java-specific evidence
  exists (2609.00362, 2607.18057, 2606.24446, 2605.06754, 2607.19682,
  2606.13298) but is thin.
- **Auditor calibration.** The blind auditors were systematically
  stricter than the first-pass reviewers: all 4 major disagreements
  moved toward rejection or a lower stance. So first-pass-only reviews
  in the KB probably overstate support slightly.

## Conflicts between papers

| Question | Side A | Side B | Reading |
| --- | --- | --- | --- |
| Do context files help? | Process efficiency gains (2607.27250) | No correctness gain (same paper); write-only for security (2608.23550) | Cheap hints, not a lever. |
| Does an LSP help agents? | Better reference precision (2608.13568) | Costs more tokens on localization (same paper) | Route by task type. |
| Are multi-agent setups worth it? | Narrow subagents +5.9 pp (2609.32459) | Generic role teams hurt (same paper); peak at N=2 (2608.23740) | Use narrow subagents, not roles. |
| Is an LLM reviewer reliable? | 96% precision at Ericsson (2609.15877) | Accuracy 0.56 on long-form; manipulable (2606.01629, 2605.26156) | The Ericsson result is author-rated and small. |
| Cheap model or expensive model? | Per-stage routing saves money (2606.22263) | Cheaper models cost more per fixed bug (2607.25333) | Measure cost per accepted change. |
| Do specs help? | Acceptance contracts help (2609.22222, 2605.17242) | More constraints hurt (2605.06445); wording flips security outcomes (2605.29737) | Short executable specs, not long prose. |

## Implications for the Java multi-repo healthcare-content team

These map onto the team's SDD sprint stages. Recommendations backed
by evidence are marked **[E]**. Engineering judgment filling a gap in
the research is marked **[J]**.

**Research and Frame (UX, Product)**
- **[E]** Measure outcomes per host and model, not by PR merge rate.
  Record CI results, reviewer commits and closure reasons for each
  agent PR (2605.22534). Add a comprehension check to review, because
  agent users understand their code less (2607.26375).
- **[E]** Start agents on narrow, well-specified changes. Treat changes
  to content schemas and templates that ripple downstream as high-risk
  (2607.21832).

**Spec (Design + Engineering)**
- **[E]** Write a spec as acceptance criteria plus a contract: OpenAPI
  or AsyncAPI for delivery endpoints, and a JSON Schema or Avro for the
  content model. Keep the prose short. Put layer, ORM and persistence
  rules in ArchUnit and static checks rather than in the spec
  (2605.06445, 2609.22222).
- **[E]** Put content semantics (field meanings, audience and licensing
  rules, versioning) in a versioned, machine-readable contract that
  agents look up per rule. Do not paste it into AGENTS.md (2609.22259).
- **[J]** For the 4+ repos: write one umbrella spec that owns the
  shared content contract, with per-repo specs that reference it by
  version. Run consumer-driven contract tests (Pact or Spring Cloud
  Contract) in every repo's CI. This is the cross-repo gate the
  research has not studied. Build it from deterministic tooling.
- **[E]** For changes that touch several repos, such as a shared
  library bump or a schema rename: have the agent write a JavaParser
  or OpenRewrite transformation once, verify it with mvn compile/test
  in one seed repo, then apply it deterministically everywhere
  (2606.24446).

**Gate (QA + Accessibility)**
- **[E]** Hard gates, the same for every host:
  - compile;
  - unit and contract tests;
  - JaCoCo diff coverage on changed lines, including catch blocks
    (2607.18057);
  - an assertion-strength check on new tests, rejecting tests that
    only call `assertNotNull` or `verify` (2606.18168);
  - containerized behavioural tests for anything touching Spring
    config, DI or packaging (2605.06754).
- **[E]** Compliance non-functional requirements (privacy of learner
  and patient data, no PHI in logs) must be executable checks: static
  rules, data-flow scans and tests. Agent self-assessment does not
  count (2606.24834).
- **[E]** LLM review is advisory only, anchored on reference examples,
  and is never the merge gate (2606.01629).
- **[J]** Accessibility for front-end delivery: the evidence is sparse
  (T58 admitted 2 papers). Keep axe or Pa11y checks deterministic and
  treat LLM repair as a suggestion.

**Harness configuration (any host)**
- **[E]** Pin host and CLI versions. Rerun a 20–50 task regression
  suite drawn from your own Java repos on every upgrade, tracking
  resolve rate, tokens and tool calls (2607.03691). Build that suite
  with leakage controls: strip future git objects, hide acceptance
  tests, block code-host egress (2609.08149).
- **[E]** Enforce permissions and egress in each host's deny/sandbox
  configuration, or in hooks. CLAUDE.md prose is not enforcement
  (2608.23550).
- **[E]** Keep AGENTS.md short: build and test commands, module test
  shortcuts, where contracts live. Lint it in CI for stale references
  and bloat (2606.15828, 2606.09090).
- **[E]** Prefer narrow subagents (contract checker, differential
  tester of old vs new ingestion output, pre-submit reviewer) over
  role teams. Use at most 2 parallel agents per task (2609.32459,
  2608.23740).
- **[E]** Avoid automatic summarization compaction on long multi-repo
  tasks. Keep state in committed files (2609.08318, 2607.17937).
- **[E]** Keep the MCP/tool catalog small and vetted (2606.04769,
  2606.14154).

## Limitations of this KB

- **Harvest bias.** Selection used our own topic queries, ranked by
  relevance with 4 papers per topic. This is not a systematic review,
  and 39 off-topic rejections show the noise. Abstract-level trend
  shares in `landscape.md` are inflated by the topic queries (RL
  appears in about 30% of abstracts).
- **Reviewers are LLMs.** Every review is one LLM pass, and only 26%
  were blind-audited. Auditors were stricter than reviewers, so
  unaudited papers may be scored slightly too high.
- **Extraction losses.** HTML-to-text conversion dropped some tables.
  One paper (2608.23552) had 8 unverifiable numbers and was rejected
  for other reasons. 1.1% of cited numbers could not be found in the
  text.
- **Preprints.** Most papers are not peer reviewed. The window closes
  on 2026-10-06, so very recent work is underrepresented.
- **Domain gap.** Almost nothing studies healthcare or education
  content pipelines, or a team's own multi-repo systems. The
  recommendations for those areas are marked [J].
