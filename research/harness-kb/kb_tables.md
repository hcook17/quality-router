# Generated KB tables

Regenerate with `python3 etl.py load && python3 etl.py report`.

Harvested unique papers: 5926. Reviews by gate status: {'caveated': 112, 'hypothesis': 36, 'no_contribution': 40, 'rejected': 90}.

Evidence = `admitted` or `caveated`: passed the review gate and the contribution
gate.
`hypothesis` and `no_contribution` passed review but add no transferable, adequately
evidenced heuristic, nuance, pattern, anti-pattern, constraint or test practice
(`CONTRIBUTION_RUBRIC.md`). They carry weight 0 and are excluded below.

## Date audit

Window: first submission (v1) 20260501–20261006. A paper first
posted earlier and only revised in the window does not qualify; the arXiv ID
prefix and the v1 `published` field are both checked by `admission`.

| Check | Result |
| --- | --- |
| Reviewed papers | 278 |
| v1 dates | 2026-05-02 … 2026-10-06 |
| v1 outside window | 0  |
| Withdrawn (rejected) | 1 2606.14066 |
| Revised since review (live arXiv recheck) | 0  |

## Contribution audit

| Outcome after review gate | Papers |
| --- | --- |
| contributes | 112 |
| no_contribution | 40 |
| hypothesis | 36 |

Qualifying contributions (evidence papers; novelty new/refines; transfers;
strength ≥ moderate):

| Kind | Items | Papers |
| --- | --- | --- |
| test_practice | 43 | 42 |
| nuance | 42 | 40 |
| heuristic | 28 | 28 |
| anti_pattern | 17 | 17 |
| design_pattern | 17 | 17 |
| constraint | 16 | 16 |

Quantity-over-quality flags (any outcome):

| Flag | Papers |
| --- | --- |
| numbers_without_mechanism | 19 |
| system_description_only | 10 |
| leaderboard_only | 8 |
| self_declared_incomplete | 8 |
| survey_restatement | 7 |
| position_without_evidence | 6 |
| renamed_known_idea | 4 |

### Hypotheses (not evidence)

| arXiv | Title | Flags |
| --- | --- | --- |
| [2605.11378](https://arxiv.org/abs/2605.11378) | An Empirical Study of Automating Agent Evaluation |  |
| [2605.12493](https://arxiv.org/abs/2605.12493) | LongMemEval-V2: Evaluating Long-Term Agent Memory Toward Experienced Colleagues | self_declared_incomplete |
| [2605.26521](https://arxiv.org/abs/2605.26521) | Testing Agentic Workflows with Structural Coverage Criteria |  |
| [2606.08500](https://arxiv.org/abs/2606.08500) | Projecting the Emerging Mindset of SWE Agent by Launching a Wild Code Understand |  |
| [2606.09090](https://arxiv.org/abs/2606.09090) | Context Rot in AI-Assisted Software Development: Repurposing Documentation Consi | renamed_known_idea, self_declared_incomplete |
| [2606.13643](https://arxiv.org/abs/2606.13643) | Recursive Agent Harnesses |  |
| [2606.15029](https://arxiv.org/abs/2606.15029) | Metric Match: A Subset Selection Approach to Evaluating LLM Judge Reliability |  |
| [2606.15828](https://arxiv.org/abs/2606.15828) | Configuration Smells in AGENTS.md Files: Common Mistakes in Configuring Coding A | survey_restatement |
| [2606.16988](https://arxiv.org/abs/2606.16988) | Agent trajectories as programs: fingerprinting and programming coding-agent beha | numbers_without_mechanism |
| [2606.20713](https://arxiv.org/abs/2606.20713) | FairTutor: Equity-Aware Pedagogical LLM Routing for Budget-Constrained AI Tutori | self_declared_incomplete |
| [2606.28436](https://arxiv.org/abs/2606.28436) | Dockerless: Environment-Free Program Verifier for Coding Agents |  |
| [2606.30317](https://arxiv.org/abs/2606.30317) | MCP Server Architecture Patterns for LLM-Integrated Applications | position_without_evidence |
| [2606.31174](https://arxiv.org/abs/2606.31174) | ClawArena-Team: Benchmarking Subagent Orchestration and Dynamic Workflows in Lan | numbers_without_mechanism |
| [2607.01942](https://arxiv.org/abs/2607.01942) | Atomic Task Graph: A Unified Framework for Agentic Planning and Execution |  |
| [2607.01980](https://arxiv.org/abs/2607.01980) | Epic-Organized vs. Requirement-Aligned Gherkin: An Empirical Evaluation of LLM-B |  |
| [2607.02882](https://arxiv.org/abs/2607.02882) | Diagnosis-Driven Automatic Repair for Agentic Workflow via Symbolic Inference |  |
| [2607.09101](https://arxiv.org/abs/2607.09101) | Multi-Agent LLM Collaboration for Unit Test Generation via Human-Testing-Inspire |  |
| [2607.18213](https://arxiv.org/abs/2607.18213) | SWE-Pruner Pro: The Coder LLM Already Knows What to Prune | numbers_without_mechanism |
| [2607.22585](https://arxiv.org/abs/2607.22585) | The Scaffold Effect in Coding Agents: Harness Choice as a Hidden Variable in Cod |  |
| [2607.27250](https://arxiv.org/abs/2607.27250) | Do Context Files Help Coding Agents? A Two-Agent Ablation Study on Real Reposito |  |
| [2607.27877](https://arxiv.org/abs/2607.27877) | An Empirical Study of Coordination Mode as the First-Class Citizen in From-Scrat | numbers_without_mechanism |
| [2608.09802](https://arxiv.org/abs/2608.09802) | SWE-Bench ProMax: Benchmarking Agents on Large-Scale Multilingual Code Refactori | leaderboard_only |
| [2608.13568](https://arxiv.org/abs/2608.13568) | Does a Language Server Save Tokens for Coding Agents? A Measurement Methodology  | self_declared_incomplete |
| [2608.16890](https://arxiv.org/abs/2608.16890) | GxP-Agent: Process-DAG Topology for Reliable Clinical Trial Programming with LLM |  |
| [2608.17694](https://arxiv.org/abs/2608.17694) | GADR: Gathering Architecture Decision Records from Meeting Transcriptions | system_description_only |
| [2608.18645](https://arxiv.org/abs/2608.18645) | Code Health in LLM-Based Test Generation: Effectiveness and Token Efficiency | numbers_without_mechanism |
| [2608.22751](https://arxiv.org/abs/2608.22751) | Risk-Aware Reranking for Agentic Tool Retrieval | numbers_without_mechanism |
| [2608.23740](https://arxiv.org/abs/2608.23740) | AgentRoom: Concurrent Multi-Agent Coding in a CRDT-Backed Shared Workspace |  |
| [2609.00050](https://arxiv.org/abs/2609.00050) | Towards Agentic Cloud Engineering: Graph and Loop Engineering with a Zero-Trust  |  |
| [2609.01861](https://arxiv.org/abs/2609.01861) | Belief-Calibrated Optimization: An Explicit World Model for Agentic Optimization |  |
| [2609.02272](https://arxiv.org/abs/2609.02272) | PaperCompiler: Faithful Paper-to-Code Generation via Repository-Level Specificat | system_description_only |
| [2609.05563](https://arxiv.org/abs/2609.05563) | Look Before You Prompt, and After: Scaffolding Human-AI Collaboration in Softwar |  |
| [2609.10871](https://arxiv.org/abs/2609.10871) | A2ABreak: Systematic Security Analysis of the A2A Protocol |  |
| [2609.36319](https://arxiv.org/abs/2609.36319) | StateTape: Action-Conditioned Evidence Lifecycle Modeling for Long-Horizon Codin | self_declared_incomplete |
| [2609.37590](https://arxiv.org/abs/2609.37590) | FOCUS: Training-Free Decision-Preserving Context Compression for LLM Agents |  |
| [2610.05300](https://arxiv.org/abs/2610.05300) | MESH-Harness: Self-Improving Agent Harnesses via Bandit-Guided Compositional Evo | leaderboard_only |

### No contribution (dropped)

| arXiv | Title | Flags |
| --- | --- | --- |
| [2605.07725](https://arxiv.org/abs/2605.07725) | SOD: Step-wise On-policy Distillation for Small Language Model Agents |  |
| [2605.08013](https://arxiv.org/abs/2605.08013) | Learning CLI Agents with Structured Action Credit under Selective Observation |  |
| [2605.15425](https://arxiv.org/abs/2605.15425) | Runtime-Structured Task Decomposition for Agentic Coding Systems | renamed_known_idea |
| [2605.18747](https://arxiv.org/abs/2605.18747) | Code as Agent Harness | survey_restatement, renamed_known_idea, position_without_evidence |
| [2605.21810](https://arxiv.org/abs/2605.21810) | Trace2Skill: Verifier-Guided Skill Evolution for Long-Context EDA Agents |  |
| [2605.22781](https://arxiv.org/abs/2605.22781) | DeltaBox: Scaling Stateful AI Agents with Millisecond-Level Sandbox Checkpoint/R |  |
| [2605.23590](https://arxiv.org/abs/2605.23590) | Co-ReAct: Rubrics as Step-Level Collaborators for ReAct Agents |  |
| [2605.24397](https://arxiv.org/abs/2605.24397) | Breaking Changes in Software Ecosystems: A Systematic Literature Review | survey_restatement |
| [2605.30898](https://arxiv.org/abs/2605.30898) | UniScale: Adaptive Unified Inference Scaling via Online Joint Optimization of Mo |  |
| [2606.09852](https://arxiv.org/abs/2606.09852) | LLM-Based Code Documentation Generation and Multi-Judge Evaluation | system_description_only, numbers_without_mechanism |
| [2606.10106](https://arxiv.org/abs/2606.10106) | What makes a harness a harness: necessary and sufficient conditions for an agent | position_without_evidence |
| [2606.14796](https://arxiv.org/abs/2606.14796) | Faster Code, Deeper Debt? A Multivocal Literature Review on Technical Debt and I | survey_restatement, position_without_evidence |
| [2606.29116](https://arxiv.org/abs/2606.29116) | Characterizing Large Language Model Agentic Workflows: A Study on N8n Ecosystem | numbers_without_mechanism, position_without_evidence |
| [2607.01456](https://arxiv.org/abs/2607.01456) | From Anatomy to Smells: An Empirical Study of SKILL.md in Agent Skills | numbers_without_mechanism, survey_restatement |
| [2607.02807](https://arxiv.org/abs/2607.02807) | SwarmResearch: Orchestrating Coding Agents for Open-Ended Discovery | numbers_without_mechanism |
| [2607.02825](https://arxiv.org/abs/2607.02825) | JavaVulBench: A Java Vulnerability Benchmark with Realistic Splits, a Unified Mu | leaderboard_only |
| [2607.21832](https://arxiv.org/abs/2607.21832) | How Do AI Coding Agents Contribute to Software Development? an Empirical Study o | numbers_without_mechanism |
| [2607.25718](https://arxiv.org/abs/2607.25718) | Tools Are Not Islands: Set-Level Tool Retrieval for LLM Agents via Query-Conditi |  |
| [2608.04588](https://arxiv.org/abs/2608.04588) | E$^3$-Orch: Towards Effective, Efficient, and Extensible Agentic Orchestration w | self_declared_incomplete, renamed_known_idea |
| [2608.05141](https://arxiv.org/abs/2608.05141) | OctoLong: Mid-Training On Cross-Repository Code Contexts Enhances Long-Context M |  |
| [2608.06848](https://arxiv.org/abs/2608.06848) | Understanding and Improving Model Editing for Secure Code Generation |  |
| [2608.07147](https://arxiv.org/abs/2608.07147) | DiDPO: Diff-in-Diff Policy Optimization for Coding Agent Training |  |
| [2608.10906](https://arxiv.org/abs/2608.10906) | GitSkills: A Dataset of Agent Skills on GitHub | system_description_only |
| [2608.11460](https://arxiv.org/abs/2608.11460) | Principal Trait Analysis: Towards Deriving "Skills" in Human-AI Collaboration | numbers_without_mechanism |
| [2608.17528](https://arxiv.org/abs/2608.17528) | Agent Lightning v1.0: Towards Harnessed Agentic RL | system_description_only |
| [2608.25202](https://arxiv.org/abs/2608.25202) | SpecMine: A Large-Scale Corpus of Spec-Driven Development Artifacts | system_description_only |
| [2608.26391](https://arxiv.org/abs/2608.26391) | Software Aging in LLM-Generated Applications: Runtime Evidence, Static Analysis, | numbers_without_mechanism |
| [2609.04219](https://arxiv.org/abs/2609.04219) | Large Language Models for Fuzz Testing in Microservices: A Systematic Literature | survey_restatement |
| [2609.07201](https://arxiv.org/abs/2609.07201) | Recompilation Is Not Enough: Test-Guided Decompiled-C Repair | self_declared_incomplete |
| [2609.08318](https://arxiv.org/abs/2609.08318) | AttnCompress: Dynamic Attention-Guided Trajectory Compression for Software Engin | numbers_without_mechanism |
| [2609.09798](https://arxiv.org/abs/2609.09798) | CS-Guard: Benchmarking LLM Guardrails for Code Generation Security | leaderboard_only |
| [2609.12464](https://arxiv.org/abs/2609.12464) | Beyond Vector Similarity: Hierarchical Context-Aware Graph RAG vs Standard RAG i | numbers_without_mechanism |
| [2609.15096](https://arxiv.org/abs/2609.15096) | OpenAI4S: Code as Action, Science as Sessions | system_description_only, numbers_without_mechanism |
| [2609.26480](https://arxiv.org/abs/2609.26480) | FeatLens: Feature-Guided Dynamic Code Graph Construction and Retrieval for Repos | numbers_without_mechanism |
| [2609.30906](https://arxiv.org/abs/2609.30906) | ToolSearcher: Optimizing Tool Selection at Scale via Reinforcement Learning | leaderboard_only |
| [2609.32631](https://arxiv.org/abs/2609.32631) | SWE-MILE: Asynchronous Potential-Induced Milestone Credit Assignment for Long-Ho | leaderboard_only |
| [2609.33762](https://arxiv.org/abs/2609.33762) | EfficientAgent: What Makes KV Cache Offloading Work for Concurrent Agents? |  |
| [2609.35811](https://arxiv.org/abs/2609.35811) | Lookahead-R: Budget-Aware Tool Retrieval via Execution-Centric Planning | leaderboard_only, numbers_without_mechanism |
| [2609.36817](https://arxiv.org/abs/2609.36817) | pikit: A Composable Toolkit for Indirect Prompt Injection Research and Evaluatio | system_description_only |
| [2609.38885](https://arxiv.org/abs/2609.38885) | Doing More with Less Tokens: Hierarchical Reinforcement Learning for Efficient C | leaderboard_only |

## Pattern evidence matrix

Evidence papers only. Weighted score = sum of review weights (rigor x reproducibility x COI discount; caveated x0.6; non-evidence 0).

| Pattern | Supports | Contradicts | Mixed | Introduces | Weighted support | Weighted contra | Vendor-authored share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P01 Hierarchical repo instruction files (AGENTS.md/CLAUDE.md) | 0 | 0 | 0 | 1 | 0.18 | 0.00 | 14% |
| P02 Progressive disclosure / skills loaded on demand | 2 | 0 | 7 | 2 | 0.89 | 0.00 | 5% |
| P03 Deferred tool loading / small tool catalog | 0 | 0 | 0 | 2 | 0.29 | 0.00 | 0% |
| P04 MCP as integration layer | 0 | 0 | 2 | 1 | 0.33 | 0.00 | 14% |
| P05 Lexical/deterministic code retrieval (grep, AST, LSP) | 3 | 0 | 7 | 3 | 1.35 | 0.00 | 8% |
| P06 Embedding/RAG retrieval over code | 2 | 1 | 4 | 1 | 0.87 | 0.24 | 17% |
| P07 Code/knowledge graph context | 3 | 1 | 1 | 1 | 0.82 | 0.24 | 0% |
| P08 Context compaction / summarization | 0 | 2 | 9 | 1 | 0.24 | 0.41 | 7% |
| P09 Persistent agent memory | 0 | 1 | 5 | 2 | 0.39 | 0.30 | 0% |
| P10 Single-agent linear loop | 0 | 0 | 4 | 0 | 0.00 | 0.00 | 0% |
| P11 Multi-agent / role-based teams | 0 | 1 | 5 | 4 | 0.73 | 0.24 | 0% |
| P12 Subagents for isolated exploration | 1 | 0 | 5 | 0 | 0.44 | 0.00 | 0% |
| P13 Planner-executor / hierarchical orchestration | 5 | 0 | 5 | 1 | 1.53 | 0.00 | 18% |
| P14 Spec-driven / spec-first development | 1 | 0 | 2 | 5 | 1.47 | 0.00 | 12% |
| P15 Test-first / TDD with agents | 2 | 1 | 2 | 0 | 0.58 | 0.24 | 0% |
| P16 Execution-based verifier loop (tests/compile) | 10 | 1 | 14 | 6 | 3.95 | 0.22 | 6% |
| P17 Static analysis / linter feedback in loop | 3 | 0 | 1 | 6 | 2.15 | 0.00 | 10% |
| P18 LLM-as-judge / AI reviewer | 1 | 2 | 12 | 2 | 0.69 | 0.66 | 12% |
| P19 Human approval gates | 0 | 0 | 2 | 4 | 0.71 | 0.00 | 22% |
| P20 OS/container sandboxing | 1 | 0 | 1 | 1 | 0.45 | 0.00 | 0% |
| P21 Policy-as-code permissions / guardrails | 6 | 0 | 2 | 4 | 2.55 | 0.00 | 4% |
| P22 Prompt-injection defenses | 1 | 1 | 3 | 2 | 0.52 | 0.30 | 7% |
| P23 Model routing / cascades | 1 | 0 | 4 | 0 | 0.29 | 0.00 | 25% |
| P24 Token/cost budgets and caps | 4 | 0 | 2 | 1 | 1.19 | 0.00 | 14% |
| P25 RL / fine-tuning of agent models | 4 | 0 | 1 | 1 | 1.27 | 0.00 | 17% |
| P26 Self-improving / searched harness | 1 | 1 | 3 | 3 | 0.97 | 0.16 | 0% |
| P27 Cross-repo coordination / contracts | 0 | 0 | 3 | 1 | 0.29 | 0.00 | 0% |
| P28 Deterministic codemods / recipe-based migration | 1 | 0 | 2 | 0 | 0.33 | 0.00 | 17% |
| P29 Parallel agents with isolated worktrees | 1 | 0 | 0 | 0 | 0.18 | 0.00 | 0% |
| P30 Observability / tracing / audit | 3 | 0 | 2 | 5 | 1.67 | 0.00 | 6% |
| P31 Benchmark-based evaluation (SWE-bench family) | 1 | 0 | 2 | 14 | 4.01 | 0.00 | 5% |
| P32 Field/industrial evaluation | 5 | 0 | 1 | 0 | 1.47 | 0.00 | 25% |
| P33 CodeAct / code-as-action / CLI-first tools | 1 | 1 | 4 | 0 | 0.22 | 0.24 | 0% |
| P34 Structured requirements / acceptance criteria | 5 | 0 | 4 | 3 | 2.26 | 0.00 | 12% |
| P35 Formal methods / verified generation | 2 | 0 | 2 | 2 | 0.87 | 0.00 | 0% |
| P36 Static workflow graph / state machine (developer-defined steps and gates) | 2 | 0 | 8 | 5 | 1.46 | 0.00 | 11% |
| P37 LLM-generated task DAG (planner emits dependencies; parallel execution) | 2 | 0 | 2 | 3 | 1.28 | 0.00 | 19% |

## Bias frequency

| Bias | Papers |
| --- | --- |
| other:audit_missed | 138 |
| no_variance_reported | 135 |
| self_evaluation | 129 |
| metric_mismatch | 128 |
| small_sample | 127 |
| closed_artifacts | 105 |
| hype_language | 79 |
| single_model | 74 |
| strawman_baseline | 70 |
| contamination_risk | 67 |
| toy_tasks | 61 |
| llm_judge_unvalidated | 61 |
| single_language_python | 50 |
| missing_cost_reporting | 42 |
| cherry_picked_examples | 38 |
| selection_bias_participants | 34 |
| self_reported_numbers | 27 |
| novelty_inflation | 27 |
| other:internal_inconsistency | 16 |
| survivorship | 14 |
| benchmark_overfit | 14 |
| other:off_topic | 7 |
| other:no_evaluation | 6 |
| other:no_limitations_section | 5 |
| other:abstract_body_mismatch | 5 |

## COI severity

| Severity | Papers | Mean rigor |
| --- | --- | --- |
| high | 11 | 1.82 |
| low | 109 | 2.30 |
| medium | 19 | 1.89 |
| none | 139 | 2.37 |

## Contribution types

| Type | Papers | Mean rigor | Rejected |
| --- | --- | --- | --- |
| empirical | 103 | 2.58 | 22 |
| system | 95 | 2.21 | 36 |
| benchmark | 27 | 2.70 | 2 |
| position | 16 | 0.94 | 15 |
| tool | 12 | 2.00 | 4 |
| survey | 10 | 1.70 | 4 |
| theory | 9 | 2.00 | 5 |
| dataset | 5 | 2.20 | 2 |
| replication | 1 | 3.00 | 0 |

## Topic coverage

| Topic | Harvested (pass gate) | Reviewed | Evidence |
| --- | --- | --- | --- |
| T01 Agent harness engineering | 200 | 4 | 1 |
| T02 Coding agent architecture | 200 | 4 | 3 |
| T03 Agent loop and control flow | 173 | 4 | 0 |
| T04 Self-improving / meta-harness | 72 | 4 | 2 |
| T05 Long-horizon autonomous coding | 165 | 4 | 3 |
| T06 Repository instruction files (AGENTS.md) | 23 | 4 | 1 |
| T07 Context engineering | 67 | 4 | 1 |
| T08 Context compaction and summarization | 63 | 4 | 2 |
| T09 Agent memory | 196 | 4 | 2 |
| T10 Skills and procedural knowledge | 200 | 4 | 2 |
| T11 Repository-level code retrieval | 178 | 4 | 3 |
| T12 Model Context Protocol | 193 | 4 | 3 |
| T13 Tool selection and catalog scale | 117 | 4 | 0 |
| T14 LSP and semantic code tools | 5 | 4 | 2 |
| T15 Code graphs and knowledge graphs | 18 | 4 | 2 |
| T16 CLI vs tool-calling vs CodeAct | 13 | 4 | 1 |
| T17 Multi-agent software engineering | 27 | 4 | 1 |
| T18 Subagents and delegation | 144 | 4 | 2 |
| T19 Orchestrator-worker and planners | 70 | 4 | 0 |
| T20 Parallel agents and merge conflicts | 20 | 4 | 0 |
| T21 Agent communication protocols | 13 | 4 | 1 |
| T22 Spec-driven development | 32 | 4 | 1 |
| T23 Requirements engineering with LLMs | 59 | 4 | 0 |
| T24 Formal specs and verification-aware generation | 59 | 4 | 3 |
| T25 Agent planning for software tasks | 70 | 4 | 2 |
| T26 Design docs and architecture by agents | 2 | 2 | 0 |
| T27 Test generation by agents | 103 | 4 | 3 |
| T28 Test-driven development with agents | 17 | 4 | 3 |
| T29 Verifier and feedback loops | 138 | 4 | 1 |
| T30 Static analysis feedback to agents | 143 | 4 | 1 |
| T31 AI code review | 83 | 4 | 2 |
| T32 LLM-as-judge reliability | 200 | 4 | 2 |
| T33 Multi-repository and cross-repo changes | 59 | 5 | 1 |
| T34 API contracts and breaking changes | 10 | 4 | 3 |
| T35 Code migration and refactoring at scale | 7 | 4 | 0 |
| T36 Dependency and build repair | 7 | 4 | 3 |
| T37 Issue-to-PR autonomy in industry | 49 | 4 | 3 |
| T38 Agent sandboxing and isolation | 165 | 4 | 1 |
| T39 Prompt injection in coding agents | 192 | 4 | 2 |
| T40 Security of agent-generated code | 12 | 4 | 2 |
| T41 Permissions, policy and guardrails | 175 | 4 | 1 |
| T42 Supply chain: skills, plugins, MCP | 105 | 4 | 1 |
| T43 Agent observability and audit | 121 | 4 | 2 |
| T44 SWE benchmark validity and contamination | 157 | 4 | 3 |
| T45 Agent evaluation methodology | 120 | 4 | 1 |
| T46 Developer productivity field studies | 28 | 4 | 3 |
| T47 Adoption and human-AI collaboration in teams | 48 | 4 | 1 |
| T48 Maintainability of agent-written code | 26 | 4 | 0 |
| T49 Model routing and cascades | 45 | 4 | 1 |
| T50 Token cost and efficiency of agents | 68 | 4 | 2 |
| T51 RL training of software agents | 59 | 4 | 0 |
| T52 Small models and distillation for agents | 56 | 4 | 0 |
| T53 Java and JVM with LLMs | 126 | 4 | 3 |
| T54 Data pipelines and ETL agents | 73 | 4 | 1 |
| T55 Schema evolution and data contracts | 5 | 4 | 1 |
| T56 Healthcare software and compliance with LLMs | 7 | 4 | 1 |
| T57 Educational content generation and quality | 2 | 2 | 0 |
| T58 Accessibility conformance with LLMs | 45 | 4 | 2 |
| T59 DAG and task-graph planning for agents | 98 | 11 | 5 |
| T60 Workflow graphs, state machines and graph runtimes | 192 | 10 | 6 |
| T61 Automated workflow generation and optimization | 48 | 10 | 5 |

## Top-weighted evidence papers

| arXiv | Title | Type | Rigor | COI | Weight |
| --- | --- | --- | --- | --- | --- |
| [2606.13298](https://arxiv.org/abs/2606.13298) | Mining Architectural Quality Under Agentic AI Adoption: A Causal Study of Java Repositorie | empirical | 4 | none | 0.48 |
| [2605.27787](https://arxiv.org/abs/2605.27787) | Long Live the Librarian! A Persistent Search Sub-Agent for Energy-Efficient Multi-Agent So | empirical | 4 | none | 0.442 |
| [2609.39154](https://arxiv.org/abs/2609.39154) | DAGent: Evaluate-then-Grow Planning for Deep Research Agents | system | 4 | none | 0.442 |
| [2608.08265](https://arxiv.org/abs/2608.08265) | Opportunity Is Not Realizability: Selection-Valid Diagnostics for Multi-LLM Routing | theory | 4 | none | 0.365 |
| [2605.06445](https://arxiv.org/abs/2605.06445) | Constraint Decay: The Fragility of LLM Agents in Backend Code Generation | empirical | 3 | none | 0.331 |
| [2606.24446](https://arxiv.org/abs/2606.24446) | Agentic Generation of AST Transformation Rules for Fixing Breaking Updates | empirical | 3 | none | 0.331 |
| [2607.03691](https://arxiv.org/abs/2607.03691) | Don't Blame the Large Language Model: How Agent Harness Evolution Shapes Coding Agent Qual | empirical | 3 | none | 0.331 |
| [2607.18057](https://arxiv.org/abs/2607.18057) | Test Coverage Analysis of Agentic Pull Requests | empirical | 3 | none | 0.331 |
| [2608.09072](https://arxiv.org/abs/2608.09072) | A Unified Issue Resolution Benchmark for Requirement Clarification, Planning, and Code Gen | benchmark | 3 | none | 0.331 |
| [2605.17242](https://arxiv.org/abs/2605.17242) | From Runnable to Shippable: Multi-Agent Test-Driven Development for Generating Full-Stack  | empirical | 3 | none | 0.331 |
| [2606.18168](https://arxiv.org/abs/2606.18168) | All Smoke, No Alarm: Oracle Signals in Agent-Authored Test Code | empirical | 3 | none | 0.331 |
| [2608.08453](https://arxiv.org/abs/2608.08453) | What Keeps Agent Skills from Being Reusable? Evidence from 138K SKILL.md Files | empirical | 3 | none | 0.331 |
| [2609.00362](https://arxiv.org/abs/2609.00362) | Revisiting Feedback-Driven LLM Code Repair: A Replication and Exploratory Java Extension | replication | 3 | none | 0.331 |
| [2609.22222](https://arxiv.org/abs/2609.22222) | Can Coding Agents Reproduce Official Statistics? Metadata, Retry Budget and the Limits of  | empirical | 3 | none | 0.331 |
| [2605.26156](https://arxiv.org/abs/2605.26156) | Turning Bias into Bugs: Bandit-Guided Style Manipulation Attacks on LLM Judges | empirical | 3 | none | 0.331 |
| [2605.29737](https://arxiv.org/abs/2605.29737) | Minimal Prompt Perturbations Lead to Code Vulnerabilities: Prompt Fragility and Hidden-Sta | empirical | 3 | none | 0.331 |
| [2606.01629](https://arxiv.org/abs/2606.01629) | Benchmarking LLM-as-a-Judge for Long-Form Output Evaluation | benchmark | 3 | none | 0.331 |
| [2606.31767](https://arxiv.org/abs/2606.31767) | JETO-Bench: A Reproducible Benchmark for Execution Time Improvement Patches in Java | benchmark | 3 | none | 0.331 |
| [2607.26375](https://arxiv.org/abs/2607.26375) | (Im)Paired Programming: Coding Agents Improve Productivity but Harm Understanding | empirical | 3 | none | 0.331 |
| [2608.06477](https://arxiv.org/abs/2608.06477) | StepJack: Benchmarking Computer-Use Agent Safety Against Multi-Step Indirect Prompt Inject | benchmark | 3 | none | 0.331 |
| [2608.25939](https://arxiv.org/abs/2608.25939) | XREPOTEST: Benchmarking Multilingual Repository-Level Unit Test Generation for Large Langu | benchmark | 3 | none | 0.331 |
| [2608.30497](https://arxiv.org/abs/2608.30497) | Bridge: Automatically Mining Ecosystem-Scale API Update Mappings and Client Update Instanc | dataset | 3 | none | 0.331 |
| [2609.27624](https://arxiv.org/abs/2609.27624) | Agent Name Collision Attacks in Multi-Agent Systems | empirical | 3 | none | 0.331 |
| [2610.02932](https://arxiv.org/abs/2610.02932) | When to Compile a Computer-Use Agent? Measuring Payback and Making Compilation Decisions f | system | 3 | none | 0.331 |
| [2607.25431](https://arxiv.org/abs/2607.25431) | CodeNib: A Multi-View Data System for Serving Repository Context to Coding Agents | system | 4 | none | 0.326 |
| [2605.11229](https://arxiv.org/abs/2605.11229) | Comment and Control: Hijacking Agentic Workflows via Context-Grounded Evolution | tool | 3 | none | 0.302 |
| [2605.22534](https://arxiv.org/abs/2605.22534) | Why Are Agentic Pull Requests Merged or Rejected? An Empirical Study | empirical | 3 | none | 0.302 |
| [2607.17619](https://arxiv.org/abs/2607.17619) | Insecure Coding Preferences in Long-Term Memory: Security Risks for LLM-based Code Generat | empirical | 3 | none | 0.302 |
| [2608.16742](https://arxiv.org/abs/2608.16742) | TDD-Agent: Test-Driven Reasoning for Code Generation | system | 3 | none | 0.302 |
| [2608.20167](https://arxiv.org/abs/2608.20167) | BreakGuard: Towards Detecting Dependency Breaking Changes with LLM-Generated Tests | empirical | 3 | none | 0.302 |
| [2608.19854](https://arxiv.org/abs/2608.19854) | Repo0: Design-Driven Zero-to-All Code Generation | system | 3 | none | 0.302 |
| [2608.25457](https://arxiv.org/abs/2608.25457) | MACGen: Toward Functionally Correct and Secure Code Generation via Multi-Agent Collaborati | system | 3 | none | 0.302 |
| [2605.06754](https://arxiv.org/abs/2605.06754) | ScarfBench: A Benchmark for Cross-Framework Application Migration in Enterprise Java | benchmark | 3 | low | 0.291 |
| [2605.15569](https://arxiv.org/abs/2605.15569) | Detecting Privilege Escalation in Polyglot Microservices via Agentic Program Analysis | system | 3 | low | 0.291 |
| [2607.16387](https://arxiv.org/abs/2607.16387) | Fantastic Adaptive Taxonomies and How to Use Them | system | 3 | low | 0.291 |
| [2608.11386](https://arxiv.org/abs/2608.11386) | The Devil Is in the Interface: Evaluating How Tool Architecture Shapes Coding Agent Behavi | empirical | 3 | low | 0.291 |
| [2609.08040](https://arxiv.org/abs/2609.08040) | VEX-Bench: Benchmarking LLM Agents for Assessing Exploitability of Software Supply Chain V | benchmark | 3 | low | 0.291 |
| [2609.22259](https://arxiv.org/abs/2609.22259) | Which Part of the Context Layer Does the Work? Separating Semantic Content from Retrieval  | empirical | 3 | low | 0.291 |
| [2609.27263](https://arxiv.org/abs/2609.27263) | Specifying and Maintaining Agentic Workflows: An Empirical Study of GitHub Agentic Workflo | empirical | 3 | low | 0.291 |
| [2606.05339](https://arxiv.org/abs/2606.05339) | A Taxonomy of Runtime Faults in Model Context Protocol Servers | empirical | 3 | low | 0.291 |

## Rejected

| arXiv | Title | Reason |
| --- | --- | --- |
| [2605.01533](https://arxiv.org/abs/2605.01533) | Genetic Programming for Self-Adaptive Auto-Scaling of Microservices | off-topic: runtime microservice auto-scaling with genetic programming. No LLM agents, coding harness, or SE-automation content. The evaluation is reasonable for |
| [2605.04449](https://arxiv.org/abs/2605.04449) | GEM: Graph-Enhanced Mixture-of-Experts with ReAct Agents for Dialogue State Trac | off-topic: dialogue state tracking on MultiWOZ, not LLM coding agents or SE. The SOTA margin is small, single-run, and against quoted baselines, and the efficie |
| [2605.04902](https://arxiv.org/abs/2605.04902) | AegisTS: A Hierarchical Agentic AI System with Reinforcement Learning for Multiv | off-topic: RL-based time-series data cleaning. 'Agentic' refers to RL policies, not LLM coding agents. The headline numbers are best cases on synthetic corrupti |
| [2605.05584](https://arxiv.org/abs/2605.05584) | Operationalizing Ethics for AI Agents: How Developers Encode Values into Reposit | Position/vision paper with no evaluation: six cherry-picked excerpts and no test of whether agents follow the encoded values. It is useful only as a pointer to  |
| [2605.05657](https://arxiv.org/abs/2605.05657) | Retrieval-Conditioned Topology Selection with Provable Budget Conservation for M | There is no end-to-end evidence: every result comes from a proxy harness, with real SWE-bench runs deferred. The headline is agreement with annotator labels aga |
| [2605.08399](https://arxiv.org/abs/2605.08399) | CoCoDA: Co-evolving Compositional DAG for Tool-Augmented Agents | Off-topic for the DAG question. The DAG is a tool-library call graph for RL-training small models on math, table QA and function-level code, not a workflow or t |
| [2605.11868](https://arxiv.org/abs/2605.11868) | IPI-proxy: An Intercepting Proxy for Red-Teaming Web-Browsing AI Agents Against  | Design description of a red-teaming tool with no empirical evaluation; usable as a pointer to an artifact but provides no evidence for the knowledge base. |
| [2605.12239](https://arxiv.org/abs/2605.12239) | Harness Engineering as Categorical Architecture | The paper's formal correspondence is definitional, and its empirical support is thin: certificate preservation holds by construction, the escalation claim rests |
| [2605.12280](https://arxiv.org/abs/2605.12280) | Iterative Audit Convergence in LLM-Managed Multi-Agent Systems: A Case Study in  | [audit tightened admit_with_caveats->reject] Unusually candid about threats and peer reviewed, but evidence is one system with no control, an author-seeded toy  |
| [2605.12652](https://arxiv.org/abs/2605.12652) | Multi-Rollout On-Policy Distillation via Peer Successes and Failures | off-topic: model post-training/distillation method for small open models; no bearing on agent harness design, and evaluation lacks seeds with config apparently  |
| [2605.12718](https://arxiv.org/abs/2605.12718) | CHAL: Council of Hierarchical Agentic Language | off-topic: multi-agent debate on philosophical/defeasible questions, not software engineering or coding-agent harnesses; evaluation uses only internal metrics w |
| [2605.15721](https://arxiv.org/abs/2605.15721) | Contexting as Recommendation: Evolutionary Collaborative Filtering for Context E | off-topic: per-instance prompt/context optimization evaluated only on NLP QA and fact-verification datasets with one model; no coding, agent, or harness evaluat |
| [2605.16821](https://arxiv.org/abs/2605.16821) | Multi-Paradigm Agent Interaction in Practice:A Systematic Analysis of Generator- | No real evaluation: one cherry-picked case study and five scenarios scored by the system's own LLM evaluator; headline abstract numbers are absent from or contr |
| [2605.17535](https://arxiv.org/abs/2605.17535) | AgentModernize: Preserving Business Logic in Legacy Modernization with Multi-Age | [audit tightened admit_with_caveats->reject] Candid paper whose most useful findings are negative (structured multi-agent pipeline loses to a single prompt on s |
| [2605.17548](https://arxiv.org/abs/2605.17548) | Rethinking Code Review in the Age of AI: A Vision for Agentic Code Review | A position paper with no implementation or evaluation, so none of its framework claims has evidence. It is a useful literature map of code-review challenges (§3 |
| [2605.19638](https://arxiv.org/abs/2605.19638) | The Accessibility Capability Boundary: Operational Limits and Expansion Potentia | Off-topic: an accessibility HCI position paper about LLM-generated single-file HTML tools, not about agent harnesses or software engineering with agents. Its em |
| [2605.25624](https://arxiv.org/abs/2605.25624) | CUA-Gym: Scaling Verifiable Training Environments and Tasks for Computer-Use Age | off-topic: RL training-data generation for GUI computer-use models. A substantial, plausibly sound dataset paper, but it informs model training, not harness des |
| [2605.26132](https://arxiv.org/abs/2605.26132) | Self-Verified Distillation: Your Language Model Is Secretly Its Own Synthetic Da | off-topic: LLM post-training on math/science/competitive-programming, not agents or software-engineering harnesses. The study is also weakened by an abstract th |
| [2605.26252](https://arxiv.org/abs/2605.26252) | Is Agent Memory a Database? Rethinking Data Foundations for Long-Term AI Agent M | Position/vision paper with no empirical evaluation. The prototype's feasibility is asserted, not measured, and the abstract overstates informal observations as  |
| [2605.26835](https://arxiv.org/abs/2605.26835) | Helicase: Uncertainty-Guided Supply Chain Knowledge Graph Construction with Auto | off-topic: supply-chain web research and knowledge-graph construction, not software engineering or coding harnesses. The evidence is also weak: an author-built  |
| [2605.28148](https://arxiv.org/abs/2605.28148) | DeltaMCP: Incremental Regeneration via Spec-Aware Transformation for MCP servers | Interesting problem framing (incremental MCP regeneration from OpenAPI diffs) but the evaluation is figure-only with inconsistent units, no numeric quality resu |
| [2605.29140](https://arxiv.org/abs/2605.29140) | S3C2 Summit 2025-07: Government Secure Supply Chain Summit | Anecdotal, unattributed practitioner discussion summary with no systematic qualitative method and internal inconsistencies; LLM content (§7) is generic (halluci |
| [2605.29226](https://arxiv.org/abs/2605.29226) | S3C2 Summit 2025-09: Industry Secure Supply Chain Summit | Practitioner-opinion summary with no systematic method; useful as an idea list (MCP default-deny, agent identities, tiered agent permissions) but provides no ev |
| [2606.01592](https://arxiv.org/abs/2606.01592) | Question Type, Cognitive Load, and CEFR Alignment: Evaluating LLM-Generated EFL  | off-topic: EFL grammar-drill learner analytics, not LLM agents or software engineering. Its headline claim that LLM-generated content is pedagogically viable is |
| [2606.03115](https://arxiv.org/abs/2606.03115) | SPOQ: Specialist Orchestrated Queuing for Multi-Agent Software Engineering | [audit tightened admit_with_caveats->reject] Useful, concrete design (dependency-wave dispatch, pre/post gates, human planning review, failure-mode catalogue in |
| [2606.03394](https://arxiv.org/abs/2606.03394) | Human-AI Collaboration and the Transformation of Software Engineering Work | Position-style synthesis with a 12-source hand-curated corpus, no search protocol, single author coding, and no empirical validation of the framework or proposi |
| [2606.05720](https://arxiv.org/abs/2606.05720) | Microskill Architecture: A Modular Skill-Driven Framework for AI-Native Code Gen | Evidence is a single unreplicated 15-feature case study with one model, a full-dump strawman baseline, no variance or ablations, a circular violations metric, u |
| [2606.07866](https://arxiv.org/abs/2606.07866) | Overcoming the Regulatory Bottleneck via Agent-to-Agent Protocols: A Nuclear Cas | off-topic: nuclear regulatory inter-organizational agent protocol, not software engineering or coding-agent harnesses; additionally, the quantitative claims are |
| [2606.13175](https://arxiv.org/abs/2606.13175) | The End of Code Review: Coding Agents Supersede Human Inspection | Provocative, well-structured position from an established SE researcher that is useful for framing merge-gate design, but its central claims are unsupported by  |
| [2606.14066](https://arxiv.org/abs/2606.14066) | FastContext: Training Efficient Repository Explorer for Coding Agents | Withdrawn by the authors (v4). Nothing can be verified. |
| [2606.15874](https://arxiv.org/abs/2606.15874) | LLM-as-Code: Agentic Programming for Agent Harness | A position paper whose single quantitative claim is an uncontrolled leaderboard comparison: baselines are not re-run, the step budget differs, a three-domain su |
| [2606.18497](https://arxiv.org/abs/2606.18497) | Ghost Vectors: Soft-Deleted Embeddings Remain Reconstructible in HNSW Vector Dat | Off-topic: vector-database storage security and erasure compliance, not LLM agents, coding agents or harness design. The evidence is also mixed: clinical claims |
| [2606.19616](https://arxiv.org/abs/2606.19616) | Before the Pull Request: Mining Multi-Agent Coordination | No LLM agents or real repositories are evaluated. The headline 78%→0% result follows from the synthetic agents' policy, Tables 1 and 2 disagree on conflicting e |
| [2606.20173](https://arxiv.org/abs/2606.20173) | Qiskit Code Migration with LLMs | Small synthetic Python benchmark, single runs, inconsistent tables, and an abstract claim ('significantly reduces hallucinations') contradicted by its own discu |
| [2606.24937](https://arxiv.org/abs/2606.24937) | The Hitchhiker's Guide to Agentic AI: From Foundations to Systems | An unreviewed, LLM-assisted textbook with no empirical contribution and no systematic review method. It can serve as a background glossary, but none of its clai |
| [2606.27416](https://arxiv.org/abs/2606.27416) | Glite ARF: Verifier-Driven Research with Parallel LLM Coding Agents | A concrete, open-source design for parallel worktree agents with deterministic spec verifiers is directly reusable. The evidence is experience-report quality: n |
| [2606.28403](https://arxiv.org/abs/2606.28403) | Reinforcement Learning for Software Vulnerability Analysis: A Systematic Review  | off-topic: classic RL for C/C++ fuzzing and vulnerability detection, not LLM agents or agent harnesses. It is also a small, unreplicable search with a prose/tab |
| [2606.30704](https://arxiv.org/abs/2606.30704) | From Search to Synthesis: Training LLMs as Zero-Shot Workflow Generators | The headline claims are not supported by the body: 'single inference' is really best-of-20 with validation selection, 'remarkable zero-shot' has a mean below th |
| [2606.31650](https://arxiv.org/abs/2606.31650) | ECHO: Prune To Act, Trace To Learn With Selective Turn Memory In Agentic RL | off-topic: an RL training recipe for long-horizon web-search agents. The team will not train policies, and the headline rests on 83 held-out items with a single |
| [2607.01640](https://arxiv.org/abs/2607.01640) | AgentFlow: Building Agent Dependency Graphs for Static Analysis of Agent Program | off-topic: analyzes the security/BOM of Python applications built on agent frameworks (LangChain, CrewAI, etc.), explicitly excluding coding agents like Claude  |
| [2607.05762](https://arxiv.org/abs/2607.05762) | Articulating Assumptions in AI-Generated Scientific Analyses through Task Decomp | off-topic: LLM code generation for collider-physics analyses, with evaluation of five hand-built task cards judged manually by the authors and no quantitative c |
| [2607.06624](https://arxiv.org/abs/2607.06624) | AgentLens: Production-Assessed Trajectory Reviews for Coding Agent Evaluation | Useful, concrete design for trajectory-level and regression evaluation of Java coding agents (Maven/Gradle verifiers, pairwise CI regression checks), but the le |
| [2607.07881](https://arxiv.org/abs/2607.07881) | Functional and Secure Code Generation with Task Vectors | off-topic for the harness KB: a sound weight-steering method for <=7B open coding models on function-level Python/C completions; it requires access to model wei |
| [2607.10532](https://arxiv.org/abs/2607.10532) | Implicit Fine-tuning via Context Engineering: A Curriculum Learning Framework fo | off-topic: multimodal knowledge-graph entity alignment with staged prompting; not about LLM agents, coding harnesses, or software engineering. |
| [2607.10736](https://arxiv.org/abs/2607.10736) | Robo-Reporters: Evaluating Autonomous AI Agents as Algorithmic Gatekeepers in Co | off-topic: journalism research agents, not software engineering; and the headline multi-agent accuracy advantage is not statistically significant (p=.066), with |
| [2607.13041](https://arxiv.org/abs/2607.13041) | LessonBench-V1: A Benchmark Dataset for Evaluating AI Lesson Generation Agents | off-topic for the harness KB and no evaluation: a lesson-plan dataset built with LLMs and an unspecified human review; the proposed benchmark is never run. Not  |
| [2607.13339](https://arxiv.org/abs/2607.13339) | Not Your Usual Type(s): Data contracts as types across languages and engines | Vendor design write-up with zero quantitative evidence; useful as a pattern description (typed contracts at pipeline boundaries, fail-fast at three stages) but  |
| [2607.15593](https://arxiv.org/abs/2607.15593) | Scalable LLM Agent Tool Access in the Cloud | A real production systems paper with useful overhead measurements, including a negative one on stateful routing. Headline efficiency gains rest on an expose-all |
| [2607.15845](https://arxiv.org/abs/2607.15845) | Knowledge-Centric Agents for Workflow Generation in ComfyUI | Off-topic: this is generation of image-generation workflows (ComfyUI), not agentic coding harness design. It does not inform a backend Java team's choice betwee |
| [2607.18555](https://arxiv.org/abs/2607.18555) | LM2Alloy: Investigating LLM-Generated Formal Specifications for Automated Test D | Interesting idea honestly framed as proof-of-concept, but evidence is one unconfirmed bug in one library, one model, Python only, and a weak baseline; the deter |
| [2607.19297](https://arxiv.org/abs/2607.19297) | Graph-Based Agentic AI with LangGraph: Workflow Pathways for Long-Running Statef | There is no evaluation; the authors say it is a recipe guide, not a benchmark. The decision heuristics are sensible but unmeasured, and benchmark results that a |
| [2607.20709](https://arxiv.org/abs/2607.20709) | NVIDIA-labs OO Agents: Native Python Object-Oriented Agents | Useful design ideas (typed validated termination, pass-by-reference code-as-action) and an informative harness feature survey, but benchmark wins are small, sin |
| [2607.21859](https://arxiv.org/abs/2607.21859) | EviDAG: Auditable Causal DAG Authoring with Biomedical Literature | Off-topic for this KB. The 'DAG' is a causal graph for epidemiological analysis, not a task or workflow graph, and the system is a literature-curation tool, not |
| [2607.22406](https://arxiv.org/abs/2607.22406) | Vibe Coding: An Experiment with Test-Driven Development | One toy Python task, 16 participants, and a model-generation confound (GPT-3.5 vs GPT-5/Sonnet 4) between arms mean the comparison cannot isolate the interactio |
| [2607.22511](https://arxiv.org/abs/2607.22511) | CausalSmith: A Formally Grounded, Self-Improving Agentic Framework for Automated | off-topic: automated mathematical research in causal inference via Lean, not software engineering; the evaluation is also self-rated with no baselines. |
| [2607.22642](https://arxiv.org/abs/2607.22642) | CRAFT: Learn the Schema, Execute the Plan | Interesting design lesson (internalize stable schemas instead of stuffing prompts) with a seeded ablation, but evidence is relative-only, closed, judge-scored,  |
| [2607.22917](https://arxiv.org/abs/2607.22917) | Agent Team Work Zone: An Automated, Persistent Workspace for Long-Lived Claude C | Admit only as a design reference for a file-backed persistence pattern. It has no evaluation at all, and every benefit claim is unsupported by the authors' own  |
| [2607.23537](https://arxiv.org/abs/2607.23537) | ObsDriveBench: Benchmarking Multimodal Understanding under Adverse Weather with  | Off-topic: an autonomous-driving vision-language benchmark under adverse weather, with no bearing on LLM coding agents, agent harnesses, or software engineering |
| [2607.24162](https://arxiv.org/abs/2607.24162) | Agent-UCT: Upper Confidence Bounds Applied to Trees for Agentic Workflow Optimiz | The central algorithmic contribution, cost-regularized UCT beating other search methods, is never tested: no competing optimizer, no lambda=0 ablation, one mode |
| [2607.28271](https://arxiv.org/abs/2607.28271) | Agentic Method for Deterministic Validation of Legacy Code Migration | Architecturally instructive industrial pattern (deterministic oracle gating agent proposals, agent repairs the deterministic migrator) but evidence is three unr |
| [2608.01001](https://arxiv.org/abs/2608.01001) | From AI Technical Debt to Agentic Technical Debt: A Systematic Mapping of Root C | Conceptual relabelling of the authors' prior AI technical-debt taxonomy with no primary evidence about agentic systems, no reported inter-rater agreement and no |
| [2608.01324](https://arxiv.org/abs/2608.01324) | G-ReAct: Graph-Guided Deep Search via Structure-State Co-Evolution | off-topic: open-web deep-search QA agent training, not coding agents or software engineering; additionally relies on unvalidated LLM judging and copied baseline |
| [2608.06112](https://arxiv.org/abs/2608.06112) | From Siloed Algorithms to Compliance-First Agentic Platforms: A Multi-Layered Ar | off-topic: hospital clinical AI platform architecture, not LLM coding agents or SE harnesses; additionally the evidence is synthetic or unverifiable, internally |
| [2608.12375](https://arxiv.org/abs/2608.12375) | Pipeline Denotational Design: Correct-by-Construction Data Pipelines at Zero Cos | No empirical evaluation: the paper's own comment and §8 state results are pending. Formal theorems rest on proof sketches and the author's own companion paper;  |
| [2608.15016](https://arxiv.org/abs/2608.15016) | Hierarchical Agentic Incident Response with Digital-Twin-Validated Attack Infere | off-topic: network-security incident response with a fine-tuned LLM and digital twin, not LLM coding agents or software engineering harnesses; also under-specif |
| [2608.16618](https://arxiv.org/abs/2608.16618) | The Specification Paradox: Rethinking Requirements Engineering in the Age of AI | Pure opinion piece with no original evaluation; the named concepts are untested relabelings and the only numbers are borrowed from other studies. Useful as voca |
| [2608.22551](https://arxiv.org/abs/2608.22551) | DAGSmith: Dependency-Aware Rewriting for dbt-Style SQL Pipelines | Off-topic for this KB. The paper is about cutting warehouse cost in SQL data pipelines; its 'DAG' is the dbt model graph being optimized, not an agent workflow  |
| [2608.23552](https://arxiv.org/abs/2608.23552) | Prime Agent: A Self-Improving RLM Harness | The headline ARC-AGI-3 number is unsupported in the body, the authors concede it does not isolate a harness effect, and the comparative table has no variance an |
| [2608.24913](https://arxiv.org/abs/2608.24913) | From Blind Edits to Verified Repair: Building Trustworthy User-Side LLM Agents f | Off-topic for this knowledge base: a user-side browser CSS-repair agent with small local models, not a software-engineering agent harness. The verified loop was |
| [2608.26171](https://arxiv.org/abs/2608.26171) | Mitigating Fabrication in Multi-Stage LLM Pipelines for Hiring: An Empirical Eva | Off-topic: an LLM hiring-content pipeline, not software engineering or agent harnesses. The study itself is carefully disclosed but rests on one human reviewer, |
| [2608.27790](https://arxiv.org/abs/2608.27790) | Credo: Reusable Declarative Primitives for Agentic Workflows | [audit tightened admit_with_caveats->reject] A clear idea with sensible checks (cost as well as accuracy in the round trip, explicit brief-only and searched ref |
| [2608.28726](https://arxiv.org/abs/2608.28726) | Pro-Router: Token-Aware Progressive Model Routing with Adaptive Edge-Cloud Colla | Off-topic: serving-layer routing for multimodal VQA with logit access to self-hosted models. It does not address coding agents or SE harnesses. Results also lac |
| [2609.00252](https://arxiv.org/abs/2609.00252) | Spec-Driven Development for Agentic Software Engineering: Harnessing Human-Agent | No empirical evidence, mechanisms largely borrowed from Hassan et al. 2025 and a search method that doesn't match how the abstract describes it. Still, it is th |
| [2609.04208](https://arxiv.org/abs/2609.04208) | AI Writes Code, Humans Pay the Debt. An Empirical Study on the Sustainability an | The pre-registered design is sound and relevant: Java, real OSS history, Sonar-family metrics, and a Stage 1 ESEM acceptance. But there are no results, so it ca |
| [2609.05529](https://arxiv.org/abs/2609.05529) | DART: A DAG-Based Reputation and Incentive Framework via Blockchain-Enabled Gove | The headline numbers are selective (one winning benchmark out of four), the coordination claim rests on one run of one task with inconsistent timings, and the D |
| [2609.05667](https://arxiv.org/abs/2609.05667) | The Impact of GenAI on the Future of Requirements Engineering | Useful, well-hedged framing of spec-driven development and RE evaluation gaps, but it is an explicitly non-systematic narrative essay with no new evidence; any  |
| [2609.05692](https://arxiv.org/abs/2609.05692) | Regret Dominates Surprise: Design-Time Requirements Engineering for Agentic-AI S | Headline simulation result is tautological (baseline evaluated with its signal disabled), the AgentHarm proxy is post-hoc, uses benchmark category labels as gat |
| [2609.20063](https://arxiv.org/abs/2609.20063) | Robust Workflow Generation via Adversarial Learning for Audio Deepfake Detection | Off-topic for coding-agent harnesses: the subject is audio deepfake detection. Beyond relevance, the abstract's 'consistently outperforms' claim is contradicted |
| [2609.21254](https://arxiv.org/abs/2609.21254) | Two's a Crowd: Human and AI-Based Copresence for Developers with ADHD | off-topic: a qualitative accessibility study of ADHD developers' copresence practices; methodologically reasonable for its genre but says nothing testable about |
| [2609.22254](https://arxiv.org/abs/2609.22254) | Teacher Should Think Ahead: Adaptive Continuations for Reliable On-Policy Distil | off-topic: a method for distilling LLM weights on math and Python function-level benchmarks, with nothing about agents, harnesses or software-engineering workfl |
| [2609.24348](https://arxiv.org/abs/2609.24348) | A Lean and Spec-Driven AI-Assisted Software Development Lifecycle for Applied AI | Useful as a concrete, released template for spec-driven development with AGENTS.md plus skills, but the evaluation is a 13-student perception survey with no con |
| [2609.24362](https://arxiv.org/abs/2609.24362) | VLM-in-Sandbox: Visual Workspaces for Agentic Visual Reasoning | off-topic: a visual-reasoning sandbox for VLMs on image QA and math benchmarks, with no software-engineering or code-agent tasks. The evaluation is reasonable,  |
| [2609.28520](https://arxiv.org/abs/2609.28520) | Certified Task-Conditioned Active Observability | off-topic: theoretical active-observability/control paper on finite Boolean systems with no LLM, agent harness, or software-engineering content. |
| [2609.28557](https://arxiv.org/abs/2609.28557) | BaseCamp --- An Agentic AI Framework for Automating DNA Sequencing Data Pipeline | Evaluation is not real: Tables 2-5 and Figures 8, 10, 11 are explicitly captioned as placeholders 'pending measurement', so every quantitative claim in the abst |
| [2609.29995](https://arxiv.org/abs/2609.29995) | Guardrails or Roadblocks? Effects of Pedagogical Style and Context Awareness in  | off-topic: classroom RCT on AI teaching-assistant prompt design for CS1 students, not LLM agents for software engineering or harness design; also omnibus-only s |
| [2609.33791](https://arxiv.org/abs/2609.33791) | Do We Really Need KL Divergence for On-Policy Distillation of Large Language Mod | off-topic: LLM distillation loss study evaluated on math and Python function-level code benchmarks; it does not concern agents, harnesses, or repository-scale s |
| [2610.02456](https://arxiv.org/abs/2610.02456) | SideKernel: A Usable microVM Sandbox for AI Coding Agents on macOS | A candid practicum report with a thorough threats-to-validity section, but the evidence is an informal survey plus single-evaluator binary tests of the author's |
| [2610.02877](https://arxiv.org/abs/2610.02877) | Evaluating LLM-as-a-Judge Beyond Score Alignment: A Psychometric Analysis of Res | off-topic: a psychometric analysis of small LLM judges on news-summary quality (SummEval). It is not about LLM agents, coding or software engineering. Methodolo |
| [2610.06829](https://arxiv.org/abs/2610.06829) | CLIFT: Conformal Self-Verification for Web Agent Training and Test-Time Scaling | off-topic: RL training and test-time selection for browser web agents, not software engineering harnesses; additionally SOTA claims rest on compute-mismatched c |
| [2610.07787](https://arxiv.org/abs/2610.07787) | OOPMAS: Object-Oriented Multi-Agent Systems for Query-Level Workflow Generation | The headline comparison is confounded by design. OOPMAS optimises each workflow against the ground-truth scorer of the very query it reports, while baselines do |

## Second-opinion audits

| Agreement | Papers |
| --- | --- |
| minor_disagreement | 104 |
| agree | 22 |
| major_disagreement | 12 |

Major disagreements (merged conservatively):

- [2605.12280](https://arxiv.org/abs/2605.12280) Iterative Audit Convergence in LLM-Managed Multi-Agent Systems: A Case Study in  — blind verdict `reject`, final `rejected`
- [2605.17535](https://arxiv.org/abs/2605.17535) AgentModernize: Preserving Business Logic in Legacy Modernization with Multi-Age — blind verdict `reject`, final `rejected`
- [2606.00579](https://arxiv.org/abs/2606.00579) Sandboxed Coding Agents are Competitive Omni-modal Task Solvers — blind verdict `admit_with_caveats`, final `caveated`
- [2606.03115](https://arxiv.org/abs/2606.03115) SPOQ: Specialist Orchestrated Queuing for Multi-Agent Software Engineering — blind verdict `reject`, final `rejected`
- [2606.18051](https://arxiv.org/abs/2606.18051) Compositional Skill Routing for LLM Agents: Decompose, Retrieve, and Compose — blind verdict `admit_with_caveats`, final `caveated`
- [2606.21338](https://arxiv.org/abs/2606.21338) "What Happens Locally, Leaks Globally": Detecting Privacy Leakage Risks in MCP S — blind verdict `admit_with_caveats`, final `caveated`
- [2607.22585](https://arxiv.org/abs/2607.22585) The Scaffold Effect in Coding Agents: Harness Choice as a Hidden Variable in Cod — blind verdict `admit_with_caveats`, final `hypothesis`
- [2608.08265](https://arxiv.org/abs/2608.08265) Opportunity Is Not Realizability: Selection-Valid Diagnostics for Multi-LLM Rout — blind verdict `admit_with_caveats`, final `caveated`
- [2608.27790](https://arxiv.org/abs/2608.27790) Credo: Reusable Declarative Primitives for Agentic Workflows — blind verdict `reject`, final `rejected`
- [2609.00006](https://arxiv.org/abs/2609.00006) Harness Engineering: Anatomy, Architecture, and Evolution of Coding Agents -- A  — blind verdict `admit_with_caveats`, final `caveated`
- [2609.01861](https://arxiv.org/abs/2609.01861) Belief-Calibrated Optimization: An Explicit World Model for Agentic Optimization — blind verdict `admit_with_caveats`, final `hypothesis`
- [2609.03086](https://arxiv.org/abs/2609.03086) Large Language Models and Language Server Protocol: a match made in context — blind verdict `admit_with_caveats`, final `caveated`
