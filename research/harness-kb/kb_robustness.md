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
| P05 Lexical/deterministic code retrieval (gr | conditional | conditional (3/0/7) | conditional | conditional | conditional | leaning | consensus | conditional | 2 |
| P06 Embedding/RAG retrieval over code | contested | contested (2/1/4) | contested | contested | contested | contested | contested | contested | 0 |
| P07 Code/knowledge graph context | contested | contested (3/1/1) | contested | contested | contested | leaning | contested | contested | 1 |
| P08 Context compaction / summarization | contested | contested (0/2/9) | contested | contested | contested | none | contested | contested | 1 |
| P09 Persistent agent memory | contested | contested (0/1/5) | contested | contested | contested | none | contested | contested | 1 |
| P10 Single-agent linear loop | thin | unresolved (0/0/4) | unresolved | unresolved | unresolved | none | unresolved | unresolved | 1 |
| P11 Multi-agent / role-based teams | contested | contested (0/1/5) | contested | contested | contested | none | unresolved | contested | 2 |
| P12 Subagents for isolated exploration | thin | unresolved (1/0/5) | unresolved | unresolved | unresolved | none | unresolved | unresolved | 1 |
| P13 Planner-executor / hierarchical orchestr | consensus | consensus (5/0/5) | consensus | consensus | consensus | none | consensus | conditional | 2 |
| P14 Spec-driven / spec-first development | thin | unresolved (1/0/2) | unresolved | leaning | unresolved | none | leaning | unresolved | 3 |
| P15 Test-first / TDD with agents | contested | contested (2/1/2) | contested | contested | contested | none | contested | contested | 1 |
| P16 Execution-based verifier loop (tests/com | conditional | conditional (10/1/14) | conditional | conditional | conditional | conditional | conditional | conditional | 0 |
| P17 Static analysis / linter feedback in loo | consensus | consensus (3/0/1) | consensus | leaning | consensus | leaning | leaning | leaning | 4 |
| P18 LLM-as-judge / AI reviewer | contested | contested (1/2/12) | contested | contested | contested | unresolved | contested | contested | 1 |
| P19 Human approval gates | - | unresolved (0/0/2) | unresolved | unresolved | unresolved | none | unresolved | unresolved | 1 |
| P20 OS/container sandboxing | thin | leaning (1/0/1) | leaning | leaning | leaning | unresolved | none | unresolved | 3 |
| P21 Policy-as-code permissions / guardrails | consensus | consensus (6/0/2) | consensus | consensus | consensus | none | consensus | consensus | 1 |
| P22 Prompt-injection defenses | contested | contested (1/1/3) | contested | contested | contested | none | contested | contested | 1 |
| P23 Model routing / cascades | - | unresolved (1/0/4) | unresolved | unresolved | unresolved | none | unresolved | unresolved | 1 |
| P24 Token/cost budgets and caps | consensus | consensus (4/0/2) | consensus | consensus | consensus | none | consensus | consensus | 1 |
| P25 RL / fine-tuning of agent models | - | consensus (4/0/1) | consensus | consensus | consensus | none | leaning | consensus | 2 |
| P26 Self-improving / searched harness | contested | contested (1/1/3) | contested | contested | contested | none | contested | contested | 1 |
| P27 Cross-repo coordination / contracts | thin | unresolved (0/0/3) | unresolved | unresolved | unresolved | unresolved | unresolved | unresolved | 0 |
| P28 Deterministic codemods / recipe-based mi | thin | unresolved (1/0/2) | leaning | unresolved | unresolved | leaning | unresolved | unresolved | 2 |
| P29 Parallel agents with isolated worktrees | - | leaning (1/0/0) | leaning | leaning | leaning | none | none | none | 3 |
| P30 Observability / tracing / audit | consensus | consensus (3/0/2) | consensus | consensus | consensus | unresolved | none | leaning | 3 |
| P31 Benchmark-based evaluation (SWE-bench fa | - | unresolved (1/0/2) | unresolved | unresolved | unresolved | none | none | unresolved | 2 |
| P32 Field/industrial evaluation | - | consensus (5/0/1) | consensus | consensus | consensus | consensus | consensus | consensus | 0 |
| P33 CodeAct / code-as-action / CLI-first too | contested | contested (1/1/4) | contested | contested | contested | none | leaning | contested | 2 |
| P34 Structured requirements / acceptance cri | consensus | consensus (5/0/4) | consensus | consensus | consensus | none | consensus | consensus | 1 |
| P35 Formal methods / verified generation | thin | leaning (2/0/2) | leaning | leaning | leaning | leaning | leaning | unresolved | 1 |
| P36 Static workflow graph / state machine (d | conditional | conditional (2/0/8) | conditional | conditional | conditional | leaning | unresolved | unresolved | 3 |
| P37 LLM-generated task DAG (planner emits de | thin | leaning (2/0/2) | leaning | leaning | leaning | none | leaning | unresolved | 2 |

Evidence papers per subset: base: 112, v1 ≤ 2026-09-30: 109, no vendor COI: 103, audited only: 112, Java-evaluated: 21, no SWE-bench: 74. Small subsets (audited, Java) lose
labels to sample size as well as to disagreement; read their flips as "this
subset alone would not support the verdict", not as a reversal.

Patterns whose label changes under at least one subset: 30.

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
| P31 | 3.77 |
| P16 | 1.39 |
| P17 | 1.35 |
| P14 | 1.23 |
| P21 | 0.94 |
| P36 | 0.92 |
| P30 | 0.87 |
| P11 | 0.73 |

## What the evidence base is made of

Full-text signal counts (`signals/*.json`), evidence papers only:

| Signal | Papers |
| --- | --- |
| Mentions Java at least 5 times | 21/112 |
| Uses SWE-bench (at least 3 mentions) | 38/112 |
| Human participants (at least 3 mentions) | 11/112 |
| Reports a statistical test or CI | 80/112 |
| Industrial setting (at least 3 mentions) | 18/112 |

## Reviewer reliability (blind second opinions)

Audited papers: 138. Agreement: {'agree': 22, 'major_disagreement': 12, 'minor_disagreement': 104}. Verdict tightened by the audit: 12.

| Score | Mean blind − original | Exact agreement |
| --- | --- | --- |
| rigor | -0.19 | 108/138 |
| reproducibility | -0.03 | 103/138 |
| generalizability | +0.09 | 103/138 |
| relevance | -0.49 | 66/138 |
| coi_risk | -0.01 | 113/138 |

`supports` stances in audited reviews: 219. The blind audit moved 139 (63%) of them: {'introduces': 29, 'mixed': 47, 'neutral': 63}.
Evidence papers without a blind audit: 0. A single review's `supports`
stance is not reliable on its own; every stance counted above has been through
the conservative audit merge.
