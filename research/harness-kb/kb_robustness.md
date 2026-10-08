# Robustness of the pattern verdicts

Regenerate with `python3 etl.py load && python3 etl.py robustness`.

Each pattern is relabelled by a fixed rule (`pattern_label` in `etl.py`) from
evidence-paper stances:

- `contested`: a contradiction weighing at least a third of the support.
- `conditional`: more mixed than supporting papers, at least 2 supporting. It
  works where measured, and most papers name a condition it needs.
- `unresolved`: more mixed than supporting papers, at most 1 supporting.
- `consensus`: at least 3 supporting papers, weighted support at least 3x the
  weighted contradiction, mixed not above supports.
- `leaning`: support below the consensus bar. `none`: no evidence paper.

`introduces` stances are excluded (a proposal is not evidence), unlike the
weighted-support column in `kb_tables.md`.
Then the label is recomputed on subsets of the evidence. A verdict that flips
under a subset rests on that subset.

| Pattern | FINDINGS.md | Rule | v1 ≤ 2026-09-30 | no vendor COI | audited only | Java-evaluated | no SWE-bench | Without top paper | Flips |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P01 Hierarchical repo instruction files (AGE | thin | none (0/0/0) | none | none | none | none | none | none | 0 |
| P02 Progressive disclosure / skills loaded o | conditional | conditional (2/0/7) | conditional | unresolved | conditional | unresolved | unresolved | unresolved | 4 |
| P03 Deferred tool loading / small tool catal | - | none (0/0/0) | none | none | none | none | none | none | 0 |
| P04 MCP as integration layer | - | unresolved (0/0/2) | unresolved | unresolved | unresolved | unresolved | unresolved | unresolved | 0 |
| P05 Lexical/deterministic code retrieval (gr | conditional | contested (3/1/9) | contested | contested | contested | leaning | consensus | contested | 2 |
| P06 Embedding/RAG retrieval over code | contested | conditional (3/1/11) | conditional | conditional | conditional | contested | contested | contested | 3 |
| P07 Code/knowledge graph context | contested | contested (3/1/5) | contested | contested | contested | leaning | contested | contested | 1 |
| P08 Context compaction / summarization | contested | contested (2/2/13) | contested | contested | contested | unresolved | contested | contested | 1 |
| P09 Persistent agent memory | contested | contested (0/1/5) | contested | contested | contested | none | contested | contested | 1 |
| P10 Single-agent linear loop | thin | unresolved (0/0/6) | unresolved | unresolved | unresolved | none | unresolved | unresolved | 1 |
| P11 Multi-agent / role-based teams | contested | contested (1/1/5) | contested | contested | contested | none | unresolved | contested | 2 |
| P12 Subagents for isolated exploration | thin | unresolved (1/0/6) | unresolved | unresolved | unresolved | none | unresolved | unresolved | 1 |
| P13 Planner-executor / hierarchical orchestr | consensus | consensus (5/0/5) | consensus | consensus | consensus | none | consensus | conditional | 2 |
| P14 Spec-driven / spec-first development | thin | unresolved (1/0/4) | unresolved | unresolved | unresolved | unresolved | unresolved | unresolved | 0 |
| P15 Test-first / TDD with agents | consensus | consensus (3/1/2) | consensus | consensus | consensus | leaning | contested | contested | 3 |
| P16 Execution-based verifier loop (tests/com | conditional | conditional (13/1/17) | conditional | conditional | conditional | conditional | conditional | conditional | 0 |
| P17 Static analysis / linter feedback in loo | consensus | consensus (4/0/2) | consensus | consensus | consensus | leaning | leaning | consensus | 2 |
| P18 LLM-as-judge / AI reviewer | contested | contested (3/4/15) | contested | contested | contested | unresolved | contested | contested | 1 |
| P19 Human approval gates | - | unresolved (0/0/2) | unresolved | unresolved | unresolved | none | unresolved | unresolved | 1 |
| P20 OS/container sandboxing | consensus | consensus (3/0/1) | consensus | consensus | consensus | unresolved | none | leaning | 3 |
| P21 Policy-as-code permissions / guardrails | consensus | consensus (6/0/3) | consensus | consensus | consensus | none | consensus | consensus | 1 |
| P22 Prompt-injection defenses | contested | contested (1/1/4) | contested | contested | contested | unresolved | contested | contested | 1 |
| P23 Model routing / cascades | - | unresolved (1/0/5) | unresolved | unresolved | unresolved | none | unresolved | unresolved | 1 |
| P24 Token/cost budgets and caps | consensus | consensus (4/0/3) | consensus | consensus | consensus | none | consensus | consensus | 1 |
| P25 RL / fine-tuning of agent models | - | consensus (4/0/2) | consensus | consensus | consensus | none | leaning | consensus | 2 |
| P26 Self-improving / searched harness | contested | contested (2/1/3) | contested | contested | contested | none | contested | contested | 1 |
| P27 Cross-repo coordination / contracts | thin | unresolved (0/0/4) | unresolved | unresolved | unresolved | unresolved | unresolved | unresolved | 0 |
| P28 Deterministic codemods / recipe-based mi | thin | unresolved (1/0/2) | leaning | unresolved | unresolved | leaning | unresolved | unresolved | 2 |
| P29 Parallel agents with isolated worktrees | thin | leaning (1/0/0) | leaning | leaning | leaning | none | none | none | 3 |
| P30 Observability / tracing / audit | consensus | consensus (4/0/2) | consensus | consensus | consensus | unresolved | none | consensus | 2 |
| P31 Benchmark-based evaluation (SWE-bench fa | - | unresolved (1/0/2) | unresolved | unresolved | unresolved | none | none | unresolved | 2 |
| P32 Field/industrial evaluation | - | consensus (5/0/1) | consensus | consensus | consensus | consensus | consensus | consensus | 0 |
| P33 CodeAct / code-as-action / CLI-first too | contested | contested (1/1/4) | contested | contested | contested | none | leaning | contested | 2 |
| P34 Structured requirements / acceptance cri | consensus | consensus (7/0/6) | consensus | consensus | consensus | unresolved | consensus | consensus | 1 |
| P35 Formal methods / verified generation | thin | leaning (2/0/2) | leaning | leaning | leaning | leaning | leaning | unresolved | 1 |
| P36 Static workflow graph / state machine (d | conditional | conditional (2/0/10) | conditional | conditional | conditional | leaning | unresolved | unresolved | 3 |
| P37 LLM-generated task DAG (planner emits de | thin | leaning (2/0/2) | leaning | leaning | leaning | none | leaning | unresolved | 2 |
| P38 Pre-spec knowledge discovery (explore co | thin | leaning (1/0/1) | leaning | leaning | leaning | none | none | unresolved | 3 |
| P39 Machine-readable domain context (cards,  | conditional | conditional (4/0/6) | conditional | conditional | conditional | unresolved | consensus | conditional | 2 |
| P40 Agent asks clarifying questions before i | thin | unresolved (0/0/4) | unresolved | unresolved | unresolved | unresolved | unresolved | unresolved | 0 |
| P41 Comprehension and skill safeguards for d | contested | contested (0/1/3) | contested | contested | contested | none | contested | contested | 1 |
| P42 Requirement-to-code traceability with ve | thin | none (0/0/0) | none | none | none | none | none | none | 0 |
| P43 Codebase question answering / exploratio | consensus | consensus (5/0/4) | consensus | consensus | consensus | unresolved | unresolved | consensus | 2 |

Evidence papers per subset: base: 152, v1 ≤ 2026-09-30: 147, no vendor COI: 140, audited only: 152, Java-evaluated: 25, no SWE-bench: 98. Small subsets (audited, Java) lose
labels to sample size as well as to disagreement; read their flips as "this
subset alone would not support the verdict", not as a reversal.

Patterns whose label changes under at least one subset: 34.

Counts in the Rule column are supports/contradicts/mixed evidence papers.

## Consensus labels the rule does not reproduce

Where `FINDINGS.md` and the rule disagree on consensus versus not.

| Pattern | FINDINGS.md | Rule | Supports/contradicts/mixed |
| --- | --- | --- | --- |
| none | | | |

## Weighted support that is only a proposal

`kb_tables.md` adds `introduces` stances to weighted support. These patterns
carry the most proposal-only weight:

| Pattern | Introduces weight |
| --- | --- |
| P31 | 6.13 |
| P18 | 2.00 |
| P17 | 1.69 |
| P16 | 1.60 |
| P05 | 1.55 |
| P43 | 1.39 |
| P21 | 1.37 |
| P42 | 1.31 |

## What the evidence base is made of

Full-text signal counts (`signals/*.json`), evidence papers only:

| Signal | Papers |
| --- | --- |
| Mentions Java at least 5 times | 25/152 |
| Uses SWE-bench (at least 3 mentions) | 54/152 |
| Human participants (at least 3 mentions) | 16/152 |
| Reports a statistical test or CI | 111/152 |
| Industrial setting (at least 3 mentions) | 20/152 |

## Reviewer reliability (blind second opinions)

Audited papers: 223. Agreement: {'agree': 54, 'major_disagreement': 12, 'minor_disagreement': 104, 'partial': 53}. Verdict tightened by the audit: 19.

| Score | Mean blind − original | Exact agreement |
| --- | --- | --- |
| rigor | -0.17 | 156/223 |
| reproducibility | +0.01 | 165/223 |
| generalizability | +0.07 | 165/223 |
| relevance | -0.33 | 116/223 |
| coi_risk | -0.02 | 185/223 |

`supports` stances in audited reviews: 266. The blind audit moved 157 (59%) of them: {'introduces': 33, 'mixed': 61, 'neutral': 63}.
Evidence papers without a blind audit: 0. A single review's `supports`
stance is not reliable on its own; every stance counted above has been through
the conservative audit merge.
