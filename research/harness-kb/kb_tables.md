# Generated KB tables

Regenerate with `python3 etl.py load && python3 etl.py report`.

Harvested unique papers: 7235. Reviews by gate status: {'caveated': 152, 'hypothesis': 65, 'no_contribution': 43, 'rejected': 167}.

Evidence = `admitted` or `caveated`: passed the review gate and the contribution
gate.
`hypothesis` and `no_contribution` passed review but add no transferable, adequately
evidenced heuristic, nuance, pattern, anti-pattern, constraint or test practice
(`CONTRIBUTION_RUBRIC.md`). They carry weight 0 and are excluded below.

## Date audit

Window: first submission (v1) 20260501–20261008. A paper first
posted earlier and only revised in the window does not qualify; the arXiv ID
prefix and the v1 `published` field are both checked by `admission`.

| Check | Result |
| --- | --- |
| Reviewed papers | 427 |
| v1 dates | 2026-05-01 … 2026-10-07 |
| v1 outside window | 0  |
| Withdrawn (rejected) | 2 2606.14066 2608.28421 |
| Revised since review (live arXiv recheck) | 0  |

## Contribution audit

| Outcome after review gate | Papers |
| --- | --- |
| contributes | 152 |
| hypothesis | 65 |
| no_contribution | 43 |

Qualifying contributions (evidence papers; novelty new/refines; transfers;
strength ≥ moderate):

| Kind | Items | Papers |
| --- | --- | --- |
| nuance | 64 | 61 |
| test_practice | 53 | 51 |
| heuristic | 49 | 47 |
| constraint | 23 | 23 |
| anti_pattern | 21 | 21 |
| design_pattern | 18 | 18 |

Quantity-over-quality flags (any outcome):

| Flag | Papers |
| --- | --- |
| numbers_without_mechanism | 23 |
| position_without_evidence | 17 |
| system_description_only | 13 |
| leaderboard_only | 11 |
| self_declared_incomplete | 11 |
| survey_restatement | 11 |
| renamed_known_idea | 7 |

### Hypotheses (not evidence)

| arXiv | Title | Flags |
| --- | --- | --- |
| [2605.11378](https://arxiv.org/abs/2605.11378) | An Empirical Study of Automating Agent Evaluation |  |
| [2605.12493](https://arxiv.org/abs/2605.12493) | LongMemEval-V2: Evaluating Long-Term Agent Memory Toward Experienced Colleagues | self_declared_incomplete |
| [2605.14563](https://arxiv.org/abs/2605.14563) | Remember Your Trace: Memory-Guided Long-Horizon Agentic Framework for Consistent |  |
| [2605.14634](https://arxiv.org/abs/2605.14634) | Documentation-Guided Agentic Codebase Migration from C to Rust |  |
| [2605.14972](https://arxiv.org/abs/2605.14972) | Viverra: Text-to-Code with Guarantees |  |
| [2605.16933](https://arxiv.org/abs/2605.16933) | The Effects of Structured LLM-Generated Feedback on Programming Assignment Perfo |  |
| [2605.21943](https://arxiv.org/abs/2605.21943) | Deterministic vs. Probabilistic Summarisation: An Empirical Trade-off Study in D |  |
| [2605.26144](https://arxiv.org/abs/2605.26144) | VISTA: An End-to-End Benchmark for Visual Spec-to-Web-App Coding Agents |  |
| [2605.26521](https://arxiv.org/abs/2605.26521) | Testing Agentic Workflows with Structural Coverage Criteria |  |
| [2605.29277](https://arxiv.org/abs/2605.29277) | Code-QA-Bench: Separating Code Reasoning from Documentation Memorization in Repo |  |
| [2606.05920](https://arxiv.org/abs/2606.05920) | Asuka-Bench: Benchmarking Code Agents on Underspecified User Intent and Multi-Ro |  |
| [2606.08500](https://arxiv.org/abs/2606.08500) | Projecting the Emerging Mindset of SWE Agent by Launching a Wild Code Understand |  |
| [2606.09090](https://arxiv.org/abs/2606.09090) | Context Rot in AI-Assisted Software Development: Repurposing Documentation Consi | renamed_known_idea, self_declared_incomplete |
| [2606.13643](https://arxiv.org/abs/2606.13643) | Recursive Agent Harnesses |  |
| [2606.15029](https://arxiv.org/abs/2606.15029) | Metric Match: A Subset Selection Approach to Evaluating LLM Judge Reliability |  |
| [2606.15828](https://arxiv.org/abs/2606.15828) | Configuration Smells in AGENTS.md Files: Common Mistakes in Configuring Coding A | survey_restatement |
| [2606.16988](https://arxiv.org/abs/2606.16988) | Agent trajectories as programs: fingerprinting and programming coding-agent beha | numbers_without_mechanism |
| [2606.18976](https://arxiv.org/abs/2606.18976) | CAPRA: Scaling Feedback on Software Architecture Deliverables with a Multi-Agent | system_description_only |
| [2606.20713](https://arxiv.org/abs/2606.20713) | FairTutor: Equity-Aware Pedagogical LLM Routing for Budget-Constrained AI Tutori | self_declared_incomplete |
| [2606.26300](https://arxiv.org/abs/2606.26300) | The Verification Horizon: No Silver Bullet for Coding Agent Rewards |  |
| [2606.28436](https://arxiv.org/abs/2606.28436) | Dockerless: Environment-Free Program Verifier for Coding Agents |  |
| [2606.30317](https://arxiv.org/abs/2606.30317) | MCP Server Architecture Patterns for LLM-Integrated Applications | position_without_evidence |
| [2606.31174](https://arxiv.org/abs/2606.31174) | ClawArena-Team: Benchmarking Subagent Orchestration and Dynamic Workflows in Lan | numbers_without_mechanism |
| [2606.31725](https://arxiv.org/abs/2606.31725) | Do Machines Struggle Where Humans Do? LLM and Human Comprehension of Obfuscated  |  |
| [2607.00711](https://arxiv.org/abs/2607.00711) | ClarifyCodeBench: Evaluating LLMs on Clarifying Ambiguous Requirements for Code  |  |
| [2607.01942](https://arxiv.org/abs/2607.01942) | Atomic Task Graph: A Unified Framework for Agentic Planning and Execution |  |
| [2607.01980](https://arxiv.org/abs/2607.01980) | Epic-Organized vs. Requirement-Aligned Gherkin: An Empirical Evaluation of LLM-B |  |
| [2607.02748](https://arxiv.org/abs/2607.02748) | Characterizing and Bridging the Diagnostic Gap in eBPF Verifier Rejections |  |
| [2607.02882](https://arxiv.org/abs/2607.02882) | Diagnosis-Driven Automatic Repair for Agentic Workflow via Symbolic Inference |  |
| [2607.05808](https://arxiv.org/abs/2607.05808) | Say What? Examining Text and Voice Input Modalities for Prompt-Based Programming |  |
| [2607.09101](https://arxiv.org/abs/2607.09101) | Multi-Agent LLM Collaboration for Unit Test Generation via Human-Testing-Inspire |  |
| [2607.15205](https://arxiv.org/abs/2607.15205) | MM-IssueLoc: A Controlled Benchmark for Evaluating Visual Evidence in Multimodal |  |
| [2607.16708](https://arxiv.org/abs/2607.16708) | Model-Driven Discipline for Multi-Agent LLMs: Requirement-to-Verification Genera |  |
| [2607.18213](https://arxiv.org/abs/2607.18213) | SWE-Pruner Pro: The Coder LLM Already Knows What to Prune | numbers_without_mechanism |
| [2607.18886](https://arxiv.org/abs/2607.18886) | TraceDev: A Traceability-Driven Multi-agent Framework for Requirement-to-Code De |  |
| [2607.22585](https://arxiv.org/abs/2607.22585) | The Scaffold Effect in Coding Agents: Harness Choice as a Hidden Variable in Cod |  |
| [2607.26390](https://arxiv.org/abs/2607.26390) | Impossible to hide secret ...: Uncovering Security and Privacy Issues in LLM-nat |  |
| [2607.27250](https://arxiv.org/abs/2607.27250) | Do Context Files Help Coding Agents? A Two-Agent Ablation Study on Real Reposito |  |
| [2607.27877](https://arxiv.org/abs/2607.27877) | An Empirical Study of Coordination Mode as the First-Class Citizen in From-Scrat | numbers_without_mechanism |
| [2608.09802](https://arxiv.org/abs/2608.09802) | SWE-Bench ProMax: Benchmarking Agents on Large-Scale Multilingual Code Refactori | leaderboard_only |
| [2608.13568](https://arxiv.org/abs/2608.13568) | Does a Language Server Save Tokens for Coding Agents? A Measurement Methodology  | self_declared_incomplete |
| [2608.16890](https://arxiv.org/abs/2608.16890) | GxP-Agent: Process-DAG Topology for Reliable Clinical Trial Programming with LLM |  |
| [2608.17694](https://arxiv.org/abs/2608.17694) | GADR: Gathering Architecture Decision Records from Meeting Transcriptions | system_description_only |
| [2608.18645](https://arxiv.org/abs/2608.18645) | Code Health in LLM-Based Test Generation: Effectiveness and Token Efficiency | numbers_without_mechanism |
| [2608.19784](https://arxiv.org/abs/2608.19784) | PRAXIS: Graph-Grounded Tacit Knowledge for Domain Code Generation |  |
| [2608.20896](https://arxiv.org/abs/2608.20896) | Beyond the Traceback: Using LLMs for Adaptive Explanations of Programming Errors | position_without_evidence |
| [2608.21531](https://arxiv.org/abs/2608.21531) | Large Language Models for Requirements Engineering: A Cross-Task Empirical Evalu | leaderboard_only |
| [2608.22751](https://arxiv.org/abs/2608.22751) | Risk-Aware Reranking for Agentic Tool Retrieval | numbers_without_mechanism |
| [2608.23740](https://arxiv.org/abs/2608.23740) | AgentRoom: Concurrent Multi-Agent Coding in a CRDT-Backed Shared Workspace |  |
| [2609.00050](https://arxiv.org/abs/2609.00050) | Towards Agentic Cloud Engineering: Graph and Loop Engineering with a Zero-Trust  |  |
| [2609.01861](https://arxiv.org/abs/2609.01861) | Belief-Calibrated Optimization: An Explicit World Model for Agentic Optimization |  |
| [2609.02272](https://arxiv.org/abs/2609.02272) | PaperCompiler: Faithful Paper-to-Code Generation via Repository-Level Specificat | system_description_only |
| [2609.05563](https://arxiv.org/abs/2609.05563) | Look Before You Prompt, and After: Scaffolding Human-AI Collaboration in Softwar |  |
| [2609.10871](https://arxiv.org/abs/2609.10871) | A2ABreak: Systematic Security Analysis of the A2A Protocol |  |
| [2609.12576](https://arxiv.org/abs/2609.12576) | A Retrieval-Augmented Automated Stakeholder for Requirements Elicitation Educati |  |
| [2609.22068](https://arxiv.org/abs/2609.22068) | CodeMidas: Scaling Agentic Coding RL Environments from Code Itself | numbers_without_mechanism |
| [2609.29208](https://arxiv.org/abs/2609.29208) | On the Impact of Requirement Smells in LLM-Based Code Generation |  |
| [2609.30334](https://arxiv.org/abs/2609.30334) | What Will Remain Human in Software Architecture? A Focus Group Report | position_without_evidence, self_declared_incomplete |
| [2609.30863](https://arxiv.org/abs/2609.30863) | Developing a Roadmap to an AI-first Organization: A Case Study in Embedded Softw | position_without_evidence, self_declared_incomplete |
| [2609.36319](https://arxiv.org/abs/2609.36319) | StateTape: Action-Conditioned Evidence Lifecycle Modeling for Long-Horizon Codin | self_declared_incomplete |
| [2609.37405](https://arxiv.org/abs/2609.37405) | Complexity-Aware Evaluation of LLM Comprehension |  |
| [2609.37590](https://arxiv.org/abs/2609.37590) | FOCUS: Training-Free Decision-Preserving Context Compression for LLM Agents |  |
| [2610.04089](https://arxiv.org/abs/2610.04089) | Pareto-Dominant Clarification: Post-Training Coding LLMs via PPO-Lagrangian Budg |  |
| [2610.05300](https://arxiv.org/abs/2610.05300) | MESH-Harness: Self-Improving Agent Harnesses via Bandit-Guided Compositional Evo | leaderboard_only |
| [2610.06910](https://arxiv.org/abs/2610.06910) | GAMEGO: Training Game-Dev Agents with Synthetic Trajectories Anchored in Real-Wo | numbers_without_mechanism |

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
| [2606.06563](https://arxiv.org/abs/2606.06563) | AI-Driven Test Case Generation from Natural Language Requirements: A Survey of T | survey_restatement, position_without_evidence |
| [2606.09852](https://arxiv.org/abs/2606.09852) | LLM-Based Code Documentation Generation and Multi-Judge Evaluation | system_description_only, numbers_without_mechanism |
| [2606.10106](https://arxiv.org/abs/2606.10106) | What makes a harness a harness: necessary and sufficient conditions for an agent | position_without_evidence |
| [2606.14796](https://arxiv.org/abs/2606.14796) | Faster Code, Deeper Debt? A Multivocal Literature Review on Technical Debt and I | survey_restatement, position_without_evidence |
| [2606.29116](https://arxiv.org/abs/2606.29116) | Characterizing Large Language Model Agentic Workflows: A Study on N8n Ecosystem | numbers_without_mechanism, position_without_evidence |
| [2606.29520](https://arxiv.org/abs/2606.29520) | SAKE: Software Architectural Knowledge Evaluation Benchmark for Large Language M | leaderboard_only |
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
| [2609.27973](https://arxiv.org/abs/2609.27973) | Understanding LLM Usage Among Early-Career Software Engineers in Practice | survey_restatement, position_without_evidence |
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
| P01 Hierarchical repo instruction files (AGENTS.md/CLAUDE.md) | 0 | 0 | 0 | 1 | 0.18 | 0.00 | 8% |
| P02 Progressive disclosure / skills loaded on demand | 2 | 0 | 7 | 4 | 1.27 | 0.00 | 12% |
| P03 Deferred tool loading / small tool catalog | 0 | 0 | 0 | 2 | 0.29 | 0.00 | 0% |
| P04 MCP as integration layer | 0 | 0 | 2 | 3 | 0.81 | 0.00 | 19% |
| P05 Lexical/deterministic code retrieval (grep, AST, LSP) | 3 | 1 | 9 | 6 | 2.22 | 0.33 | 6% |
| P06 Embedding/RAG retrieval over code | 3 | 1 | 11 | 2 | 1.56 | 0.24 | 14% |
| P07 Code/knowledge graph context | 3 | 1 | 5 | 4 | 1.73 | 0.24 | 7% |
| P08 Context compaction / summarization | 2 | 2 | 13 | 1 | 0.70 | 0.41 | 10% |
| P09 Persistent agent memory | 0 | 1 | 5 | 2 | 0.39 | 0.30 | 0% |
| P10 Single-agent linear loop | 0 | 0 | 6 | 0 | 0.00 | 0.00 | 6% |
| P11 Multi-agent / role-based teams | 1 | 1 | 5 | 6 | 1.34 | 0.24 | 7% |
| P12 Subagents for isolated exploration | 1 | 0 | 6 | 4 | 1.59 | 0.00 | 7% |
| P13 Planner-executor / hierarchical orchestration | 5 | 0 | 5 | 1 | 1.53 | 0.00 | 18% |
| P14 Spec-driven / spec-first development | 1 | 0 | 4 | 5 | 1.47 | 0.00 | 10% |
| P15 Test-first / TDD with agents | 3 | 1 | 2 | 0 | 0.87 | 0.24 | 0% |
| P16 Execution-based verifier loop (tests/compile) | 13 | 1 | 17 | 7 | 4.82 | 0.22 | 7% |
| P17 Static analysis / linter feedback in loop | 4 | 0 | 2 | 7 | 2.77 | 0.00 | 8% |
| P18 LLM-as-judge / AI reviewer | 3 | 4 | 15 | 9 | 2.77 | 1.23 | 12% |
| P19 Human approval gates | 0 | 0 | 2 | 6 | 1.14 | 0.00 | 15% |
| P20 OS/container sandboxing | 3 | 0 | 1 | 1 | 0.97 | 0.00 | 0% |
| P21 Policy-as-code permissions / guardrails | 6 | 0 | 3 | 6 | 2.99 | 0.00 | 4% |
| P22 Prompt-injection defenses | 1 | 1 | 4 | 2 | 0.52 | 0.30 | 7% |
| P23 Model routing / cascades | 1 | 0 | 5 | 0 | 0.29 | 0.00 | 23% |
| P24 Token/cost budgets and caps | 4 | 0 | 3 | 2 | 1.52 | 0.00 | 15% |
| P25 RL / fine-tuning of agent models | 4 | 0 | 2 | 2 | 1.47 | 0.00 | 12% |
| P26 Self-improving / searched harness | 2 | 1 | 3 | 3 | 1.10 | 0.16 | 0% |
| P27 Cross-repo coordination / contracts | 0 | 0 | 4 | 1 | 0.29 | 0.00 | 0% |
| P28 Deterministic codemods / recipe-based migration | 1 | 0 | 2 | 0 | 0.33 | 0.00 | 14% |
| P29 Parallel agents with isolated worktrees | 1 | 0 | 0 | 0 | 0.18 | 0.00 | 0% |
| P30 Observability / tracing / audit | 4 | 0 | 2 | 5 | 2.00 | 0.00 | 6% |
| P31 Benchmark-based evaluation (SWE-bench family) | 1 | 0 | 2 | 22 | 6.37 | 0.00 | 7% |
| P32 Field/industrial evaluation | 5 | 0 | 1 | 3 | 1.98 | 0.00 | 29% |
| P33 CodeAct / code-as-action / CLI-first tools | 1 | 1 | 4 | 0 | 0.22 | 0.24 | 0% |
| P34 Structured requirements / acceptance criteria | 7 | 0 | 6 | 5 | 3.19 | 0.00 | 8% |
| P35 Formal methods / verified generation | 2 | 0 | 2 | 3 | 1.04 | 0.00 | 0% |
| P36 Static workflow graph / state machine (developer-defined steps and gates) | 2 | 0 | 10 | 6 | 1.59 | 0.00 | 13% |
| P37 LLM-generated task DAG (planner emits dependencies; parallel execution) | 2 | 0 | 2 | 4 | 1.57 | 0.00 | 18% |
| P38 Pre-spec knowledge discovery (explore code, docs and people before writing the spec) | 1 | 0 | 1 | 4 | 1.32 | 0.00 | 15% |
| P39 Machine-readable domain context (cards, glossaries, ontologies, data contracts) | 4 | 0 | 6 | 4 | 1.83 | 0.00 | 10% |
| P40 Agent asks clarifying questions before implementing | 0 | 0 | 4 | 3 | 0.66 | 0.00 | 7% |
| P41 Comprehension and skill safeguards for developers (walkthroughs, explanations, learning modes) | 0 | 1 | 3 | 3 | 0.82 | 0.33 | 0% |
| P42 Requirement-to-code traceability with verified links | 0 | 0 | 0 | 5 | 1.31 | 0.00 | 12% |
| P43 Codebase question answering / exploration agents | 5 | 0 | 4 | 5 | 3.03 | 0.00 | 16% |

## Bias frequency

| Bias | Papers |
| --- | --- |
| other:audit_missed | 223 |
| metric_mismatch | 216 |
| no_variance_reported | 205 |
| small_sample | 200 |
| self_evaluation | 192 |
| closed_artifacts | 162 |
| hype_language | 144 |
| single_model | 115 |
| strawman_baseline | 114 |
| contamination_risk | 106 |
| llm_judge_unvalidated | 101 |
| toy_tasks | 92 |
| single_language_python | 80 |
| missing_cost_reporting | 69 |
| cherry_picked_examples | 66 |
| selection_bias_participants | 61 |
| novelty_inflation | 51 |
| self_reported_numbers | 50 |
| benchmark_overfit | 29 |
| survivorship | 22 |
| other:internal_inconsistency | 21 |
| other:off_topic | 13 |
| other:no_evaluation | 9 |
| other:abstract_body_mismatch | 7 |
| other:no_baseline | 6 |

## COI severity

| Severity | Papers | Mean rigor |
| --- | --- | --- |
| high | 18 | 1.78 |
| low | 154 | 2.25 |
| medium | 34 | 1.88 |
| none | 221 | 2.29 |

## Contribution types

| Type | Papers | Mean rigor | Rejected |
| --- | --- | --- | --- |
| empirical | 156 | 2.51 | 41 |
| system | 151 | 2.10 | 73 |
| benchmark | 48 | 2.71 | 8 |
| position | 24 | 0.88 | 23 |
| tool | 18 | 1.72 | 9 |
| survey | 11 | 1.73 | 4 |
| theory | 10 | 1.80 | 6 |
| dataset | 8 | 2.12 | 3 |
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
| T62 Codebase comprehension and developer onboarding | 102 | 26 | 10 |
| T63 Requirement clarification and ambiguity handling by agents | 177 | 25 | 9 |
| T64 Domain knowledge and enterprise context for coding agents | 253 | 25 | 3 |
| T65 Codebase question answering and exploration agents | 26 | 14 | 11 |
| T66 Documentation generation and knowledge capture | 61 | 25 | 4 |
| T67 Developer learning, skill formation and comprehension with AI | 50 | 14 | 1 |
| T68 Requirements traceability and specification recovery | 267 | 28 | 4 |
| T69 Change impact analysis and issue understanding | 35 | 10 | 5 |

## Top-weighted evidence papers

| arXiv | Title | Type | Rigor | COI | Weight |
| --- | --- | --- | --- | --- | --- |
| [2606.13298](https://arxiv.org/abs/2606.13298) | Mining Architectural Quality Under Agentic AI Adoption: A Causal Study of Java Repositorie | empirical | 4 | none | 0.48 |
| [2605.17965](https://arxiv.org/abs/2605.17965) | BLAgent: Agentic RAG for File-Level Bug Localization | empirical | 4 | none | 0.442 |
| [2605.27787](https://arxiv.org/abs/2605.27787) | Long Live the Librarian! A Persistent Search Sub-Agent for Energy-Efficient Multi-Agent So | empirical | 4 | none | 0.442 |
| [2609.39154](https://arxiv.org/abs/2609.39154) | DAGent: Evaluate-then-Grow Planning for Deep Research Agents | system | 4 | none | 0.442 |
| [2605.09698](https://arxiv.org/abs/2605.09698) | Ambig-DS: A Benchmark for Task-Framing Ambiguity in Data-Science Agents | benchmark | 4 | none | 0.365 |
| [2607.01810](https://arxiv.org/abs/2607.01810) | Decoupling Code Complexity from Newcomer Participation: A Causal Study of AI Coding Agent  | empirical | 4 | none | 0.365 |
| [2608.08265](https://arxiv.org/abs/2608.08265) | Opportunity Is Not Realizability: Selection-Valid Diagnostics for Multi-LLM Routing | theory | 4 | none | 0.365 |
| [2605.06445](https://arxiv.org/abs/2605.06445) | Constraint Decay: The Fragility of LLM Agents in Backend Code Generation | empirical | 3 | none | 0.331 |
| [2606.07297](https://arxiv.org/abs/2606.07297) | SWE-Explore: Benchmarking How Coding Agents Explore Repositories | benchmark | 3 | none | 0.331 |
| [2606.24446](https://arxiv.org/abs/2606.24446) | Agentic Generation of AST Transformation Rules for Fixing Breaking Updates | empirical | 3 | none | 0.331 |
| [2607.03691](https://arxiv.org/abs/2607.03691) | Don't Blame the Large Language Model: How Agent Harness Evolution Shapes Coding Agent Qual | empirical | 3 | none | 0.331 |
| [2607.11111](https://arxiv.org/abs/2607.11111) | Know Before Fix: QA-Driven Repository Knowledge Acquisition for Software Issue Resolution | system | 3 | none | 0.331 |
| [2607.18057](https://arxiv.org/abs/2607.18057) | Test Coverage Analysis of Agentic Pull Requests | empirical | 3 | none | 0.331 |
| [2608.09072](https://arxiv.org/abs/2608.09072) | A Unified Issue Resolution Benchmark for Requirement Clarification, Planning, and Code Gen | benchmark | 3 | none | 0.331 |
| [2605.17242](https://arxiv.org/abs/2605.17242) | From Runnable to Shippable: Multi-Agent Test-Driven Development for Generating Full-Stack  | empirical | 3 | none | 0.331 |
| [2605.26563](https://arxiv.org/abs/2605.26563) | TrajAudit: Automated Failure Diagnosis for Agentic Coding Systems | empirical | 3 | none | 0.331 |
| [2606.18168](https://arxiv.org/abs/2606.18168) | All Smoke, No Alarm: Oracle Signals in Agent-Authored Test Code | empirical | 3 | none | 0.331 |
| [2607.08885](https://arxiv.org/abs/2607.08885) | Programmers Are Poor and Overconfident Judges of LLM-Generated Assertions | empirical | 3 | none | 0.331 |
| [2607.11046](https://arxiv.org/abs/2607.11046) | Retrieval-Oriented Code Representations in Agentic Bug Localization | empirical | 3 | none | 0.331 |
| [2608.08453](https://arxiv.org/abs/2608.08453) | What Keeps Agent Skills from Being Reusable? Evidence from 138K SKILL.md Files | empirical | 3 | none | 0.331 |
| [2608.29675](https://arxiv.org/abs/2608.29675) | Cost-Effective Repository Exploration for Agentic Issue Localization | empirical | 3 | none | 0.331 |
| [2608.30686](https://arxiv.org/abs/2608.30686) | Beyond the Payload: How User Invocation Shapes Coding Agent Vulnerability to Repository Po | benchmark | 3 | none | 0.331 |
| [2609.00362](https://arxiv.org/abs/2609.00362) | Revisiting Feedback-Driven LLM Code Repair: A Replication and Exploratory Java Extension | replication | 3 | none | 0.331 |
| [2609.22222](https://arxiv.org/abs/2609.22222) | Can Coding Agents Reproduce Official Statistics? Metadata, Retry Budget and the Limits of  | empirical | 3 | none | 0.331 |
| [2605.26156](https://arxiv.org/abs/2605.26156) | Turning Bias into Bugs: Bandit-Guided Style Manipulation Attacks on LLM Judges | empirical | 3 | none | 0.331 |
| [2605.29737](https://arxiv.org/abs/2605.29737) | Minimal Prompt Perturbations Lead to Code Vulnerabilities: Prompt Fragility and Hidden-Sta | empirical | 3 | none | 0.331 |
| [2606.01629](https://arxiv.org/abs/2606.01629) | Benchmarking LLM-as-a-Judge for Long-Form Output Evaluation | benchmark | 3 | none | 0.331 |
| [2606.31767](https://arxiv.org/abs/2606.31767) | JETO-Bench: A Reproducible Benchmark for Execution Time Improvement Patches in Java | benchmark | 3 | none | 0.331 |
| [2607.00911](https://arxiv.org/abs/2607.00911) | From Registry to Repository: How AI Agent Skills Are Written, Adapted, and Maintained | empirical | 3 | none | 0.331 |
| [2607.26375](https://arxiv.org/abs/2607.26375) | (Im)Paired Programming: Coding Agents Improve Productivity but Harm Understanding | empirical | 3 | none | 0.331 |
| [2608.06477](https://arxiv.org/abs/2608.06477) | StepJack: Benchmarking Computer-Use Agent Safety Against Multi-Step Indirect Prompt Inject | benchmark | 3 | none | 0.331 |
| [2608.23619](https://arxiv.org/abs/2608.23619) | Identifying Latent Declarative Representations of Code for Assisting Repository Migration | system | 3 | none | 0.331 |
| [2608.25939](https://arxiv.org/abs/2608.25939) | XREPOTEST: Benchmarking Multilingual Repository-Level Unit Test Generation for Large Langu | benchmark | 3 | none | 0.331 |
| [2608.30497](https://arxiv.org/abs/2608.30497) | Bridge: Automatically Mining Ecosystem-Scale API Update Mappings and Client Update Instanc | dataset | 3 | none | 0.331 |
| [2609.27624](https://arxiv.org/abs/2609.27624) | Agent Name Collision Attacks in Multi-Agent Systems | empirical | 3 | none | 0.331 |
| [2610.02932](https://arxiv.org/abs/2610.02932) | When to Compile a Computer-Use Agent? Measuring Payback and Making Compilation Decisions f | system | 3 | none | 0.331 |
| [2607.25431](https://arxiv.org/abs/2607.25431) | CodeNib: A Multi-View Data System for Serving Repository Context to Coding Agents | system | 4 | none | 0.326 |
| [2605.11229](https://arxiv.org/abs/2605.11229) | Comment and Control: Hijacking Agentic Workflows via Context-Grounded Evolution | tool | 3 | none | 0.302 |
| [2605.22534](https://arxiv.org/abs/2605.22534) | Why Are Agentic Pull Requests Merged or Rejected? An Empirical Study | empirical | 3 | none | 0.302 |
| [2607.17619](https://arxiv.org/abs/2607.17619) | Insecure Coding Preferences in Long-Term Memory: Security Risks for LLM-based Code Generat | empirical | 3 | none | 0.302 |

## Rejected

| arXiv | Title | Reason |
| --- | --- | --- |
| [2605.01423](https://arxiv.org/abs/2605.01423) | HepScript: A Dual-Use DSL for Human-AI Collaborative Data Analysis Workflows in  | Off-topic. This is a BESIII analysis DSL, not software development, onboarding, or codebase exploration. The retry loop is a real measurement (about 45% to abou |
| [2605.01533](https://arxiv.org/abs/2605.01533) | Genetic Programming for Self-Adaptive Auto-Scaling of Microservices | off-topic: runtime microservice auto-scaling with genetic programming. No LLM agents, coding harness, or SE-automation content. The evaluation is reasonable for |
| [2605.04449](https://arxiv.org/abs/2605.04449) | GEM: Graph-Enhanced Mixture-of-Experts with ReAct Agents for Dialogue State Trac | off-topic: dialogue state tracking on MultiWOZ, not LLM coding agents or SE. The SOTA margin is small, single-run, and against quoted baselines, and the efficie |
| [2605.04637](https://arxiv.org/abs/2605.04637) | SWE-WebDevBench: Evaluating Coding Agent Application Platforms as Virtual Softwa | Vendor-graded and unblinded, with 18 single-run cells and no statistics; the headline causal statements ('strongly predicts', the 10-15% elicitation share) are  |
| [2605.04902](https://arxiv.org/abs/2605.04902) | AegisTS: A Hierarchical Agentic AI System with Reinforcement Learning for Multiv | off-topic: RL-based time-series data cleaning. 'Agentic' refers to RL policies, not LLM coding agents. The headline numbers are best cases on synthetic corrupti |
| [2605.05400](https://arxiv.org/abs/2605.05400) | Mise en Place for Agentic Coding: Deliberate Preparation as Context Engineering  | A practice proposal backed by a single uncontrolled self-report with no outcome measure; the efficacy statements are unsupported by the body. The gate rejects a |
| [2605.05584](https://arxiv.org/abs/2605.05584) | Operationalizing Ethics for AI Agents: How Developers Encode Values into Reposit | Position/vision paper with no evaluation: six cherry-picked excerpts and no test of whether agents follow the encoded values. It is useful only as a pointer to  |
| [2605.05657](https://arxiv.org/abs/2605.05657) | Retrieval-Conditioned Topology Selection with Provable Budget Conservation for M | There is no end-to-end evidence: every result comes from a proxy harness, with real SWE-bench runs deferred. The headline is agreement with annotator labels aga |
| [2605.06910](https://arxiv.org/abs/2605.06910) | Benchmarking Large Language Models for IoC Recovery under Adversarial Code Obfus | Off-topic: this is LLM-assisted security analysis (extracting threat indicators from obfuscated malware-like JavaScript), not software development with LLMs or  |
| [2605.07068](https://arxiv.org/abs/2605.07068) | WiCER: Wiki-memory Compile, Evaluate, Refine Iterative Knowledge Compilation for | Off-topic for this KB: knowledge compilation for document QA by a local model, not software development with LLMs or agents, nor its human side. Independently,  |
| [2605.08399](https://arxiv.org/abs/2605.08399) | CoCoDA: Co-evolving Compositional DAG for Tool-Augmented Agents | Off-topic for the DAG question. The DAG is a tool-library call graph for RL-training small models on math, table QA and function-level code, not a workflow or t |
| [2605.09055](https://arxiv.org/abs/2605.09055) | Octopus Protocol: One-Shot Hardware Discovery and Control for AI Agents via Infr | Off scope for this KB question. 'Onboarding' here means attaching physical devices, not onboarding developers or discovering requirements. The evaluation is a s |
| [2605.10865](https://arxiv.org/abs/2605.10865) | BenchCAD: A Comprehensive, Industry-Standard Benchmark for Programmatic CAD | Off-topic for this KB. It evaluates multimodal generation of mechanical CAD programs, not software development practice, agent harnesses, or the human side of d |
| [2605.11027](https://arxiv.org/abs/2605.11027) | From Code-Centric to Intent-Centric Software Engineering: A Reflexive Thematic A | The paper is on the team's problem (intent, evidence gates, accountability) but it is one researcher's reading of public figures and familiar SE citations. It d |
| [2605.11868](https://arxiv.org/abs/2605.11868) | IPI-proxy: An Intercepting Proxy for Red-Teaming Web-Browsing AI Agents Against  | Design description of a red-teaming tool with no empirical evaluation; usable as a pointer to an artifact but provides no evidence for the knowledge base. |
| [2605.12239](https://arxiv.org/abs/2605.12239) | Harness Engineering as Categorical Architecture | The paper's formal correspondence is definitional, and its empirical support is thin: certificate preservation holds by construction, the escalation claim rests |
| [2605.12280](https://arxiv.org/abs/2605.12280) | Iterative Audit Convergence in LLM-Managed Multi-Agent Systems: A Case Study in  | [audit tightened admit_with_caveats->reject] Unusually candid about threats and peer reviewed, but evidence is one system with no control, an author-seeded toy  |
| [2605.12652](https://arxiv.org/abs/2605.12652) | Multi-Rollout On-Policy Distillation via Peer Successes and Failures | off-topic: model post-training/distillation method for small open models; no bearing on agent harness design, and evaluation lacks seeds with config apparently  |
| [2605.12718](https://arxiv.org/abs/2605.12718) | CHAL: Council of Hierarchical Agentic Language | off-topic: multi-agent debate on philosophical/defeasible questions, not software engineering or coding-agent harnesses; evaluation uses only internal metrics w |
| [2605.13950](https://arxiv.org/abs/2605.13950) | Collider-Bench: Benchmarking AI Agents with Particle Physics Analysis Reproducti | Off-topic. Collider-Bench measures whether agents can recast LHC searches, not software development, onboarding, or repository question answering. The three-run |
| [2605.15334](https://arxiv.org/abs/2605.15334) | From I/O to Code with Discovery Agent | Off-topic for this KB: this is inductive program synthesis on oracle-generated toy functions, not software-development practice or a harness for pre-spec discov |
| [2605.15721](https://arxiv.org/abs/2605.15721) | Contexting as Recommendation: Evolutionary Collaborative Filtering for Context E | off-topic: per-instance prompt/context optimization evaluated only on NLP QA and fact-verification datasets with one model; no coding, agent, or harness evaluat |
| [2605.16821](https://arxiv.org/abs/2605.16821) | Multi-Paradigm Agent Interaction in Practice:A Systematic Analysis of Generator- | No real evaluation: one cherry-picked case study and five scenarios scored by the system's own LLM evaluator; headline abstract numbers are absent from or contr |
| [2605.17535](https://arxiv.org/abs/2605.17535) | AgentModernize: Preserving Business Logic in Legacy Modernization with Multi-Age | [audit tightened admit_with_caveats->reject] Candid paper whose most useful findings are negative (structured multi-agent pipeline loses to a single prompt on s |
| [2605.17548](https://arxiv.org/abs/2605.17548) | Rethinking Code Review in the Age of AI: A Vision for Agentic Code Review | A position paper with no implementation or evaluation, so none of its framework claims has evidence. It is a useful literature map of code-review challenges (§3 |
| [2605.17675](https://arxiv.org/abs/2605.17675) | Bridging the Gap on AI-Assisted Scientific Software Development Through Transpar | The governance claims are unmeasured, and 'AGENTS.md reduced hallucination' is unsupported. The value is a documented field report from a QA-regulated open-sour |
| [2605.18684](https://arxiv.org/abs/2605.18684) | Reversa: A Reverse Documentation Engineering Framework for Converting Legacy Sof | A design description with one self-graded toy case study, no baseline, an unreported model, and a migration whose parity was never verified. The abstract is hon |
| [2605.19638](https://arxiv.org/abs/2605.19638) | The Accessibility Capability Boundary: Operational Limits and Expansion Potentia | Off-topic: an accessibility HCI position paper about LLM-generated single-file HTML tools, not about agent harnesses or software engineering with agents. Its em |
| [2605.20456](https://arxiv.org/abs/2605.20456) | Agentic Agile-V: From Vibe Coding to Verified Engineering in Software and Hardwa | The cited split between enterprise speedup and open-source slowdown, and between helpful and harmful repository instructions, is a fair reading of other studies |
| [2605.21532](https://arxiv.org/abs/2605.21532) | Contract Based Verification of Non-functional Requirements for Embedded Automoti | A sound tool paper on a real industrial target with honest discussion. The LLM side experiment is tiny and cherry-picked, and the introduction's 'satisfy all ve |
| [2605.24883](https://arxiv.org/abs/2605.24883) | Inverting the Shield: Systematically Generating Safety Tests from Policy Specifi | Off-topic. This is LLM safety red-teaming, not software development with LLMs or agents, and not the human side of it. In its own field the headline comparison  |
| [2605.25297](https://arxiv.org/abs/2605.25297) | Eureka: Intelligent Feature Engineering for Enterprise AI Cloud Resource Demand  | Off-topic: tabular ML feature engineering, not software development with agents. Within its own field the headline 'consistently outperforms' is contradicted by |
| [2605.25624](https://arxiv.org/abs/2605.25624) | CUA-Gym: Scaling Verifiable Training Environments and Tasks for Computer-Use Age | off-topic: RL training-data generation for GUI computer-use models. A substantial, plausibly sound dataset paper, but it informs model training, not harness des |
| [2605.25977](https://arxiv.org/abs/2605.25977) | Creative Quality Alignment: Expert Tacit Knowledge Transfer via Chain-of-Thought | Off-topic (creative-writing alignment). Within its own scope, the primary result comes from a checkpoint chosen post hoc with no correction. The ablation is ref |
| [2605.26132](https://arxiv.org/abs/2605.26132) | Self-Verified Distillation: Your Language Model Is Secretly Its Own Synthetic Da | off-topic: LLM post-training on math/science/competitive-programming, not agents or software-engineering harnesses. The study is also weakened by an abstract th |
| [2605.26252](https://arxiv.org/abs/2605.26252) | Is Agent Memory a Database? Rethinking Data Foundations for Long-Term AI Agent M | Position/vision paper with no empirical evaluation. The prototype's feasibility is asserted, not measured, and the abstract overstates informal observations as  |
| [2605.26835](https://arxiv.org/abs/2605.26835) | Helicase: Uncertainty-Guided Supply Chain Knowledge Graph Construction with Auto | off-topic: supply-chain web research and knowledge-graph construction, not software engineering or coding harnesses. The evidence is also weak: an author-built  |
| [2605.28148](https://arxiv.org/abs/2605.28148) | DeltaMCP: Incremental Regeneration via Spec-Aware Transformation for MCP servers | Interesting problem framing (incremental MCP regeneration from OpenAPI diffs) but the evaluation is figure-only with inconsistent units, no numeric quality resu |
| [2605.29140](https://arxiv.org/abs/2605.29140) | S3C2 Summit 2025-07: Government Secure Supply Chain Summit | Anecdotal, unattributed practitioner discussion summary with no systematic qualitative method and internal inconsistencies; LLM content (§7) is generic (halluci |
| [2605.29226](https://arxiv.org/abs/2605.29226) | S3C2 Summit 2025-09: Industry Secure Supply Chain Summit | Practitioner-opinion summary with no systematic method; useful as an idea list (MCP default-deny, agent identities, tiered agent permissions) but provides no ev |
| [2605.29786](https://arxiv.org/abs/2605.29786) | Croissant Tasks: A Metadata Format for Reproducible Machine Learning Evaluations | Off-topic. This is a metadata format for reproducing machine-learning benchmarks, not a study of software development, codebase discovery, or developer learning |
| [2605.30353](https://arxiv.org/abs/2605.30353) | Physics Is All You Need? A Case Study in Physicist-Supervised AI Development of  | An honest, artifact-backed N=1 case study with a clear limitations section and a public development log, useful as an illustrative failure taxonomy. However, th |
| [2605.30995](https://arxiv.org/abs/2605.30995) | Traceable by Design: An LLM Pipeline and Dashboard for EU Regulatory Consultatio | Off-topic for a software-development harness KB. It is also a system description without an evaluation of extraction quality: the only number is a string-match  |
| [2605.31268](https://arxiv.org/abs/2605.31268) | Mellum2 Technical Report | A vendor model card with no harness, discovery or repository-level evidence. The agentic-coding framing is unevaluated, and results are single-run self-evaluati |
| [2606.01592](https://arxiv.org/abs/2606.01592) | Question Type, Cognitive Load, and CEFR Alignment: Evaluating LLM-Generated EFL  | off-topic: EFL grammar-drill learner analytics, not LLM agents or software engineering. Its headline claim that LLM-generated content is pedagogically viable is |
| [2606.02834](https://arxiv.org/abs/2606.02834) | Large Byte Model: Teaching Language Models About Compiled Code | Off-topic (malware classification). It also has high COI, mismatched baseline evaluation, a novelty claim contradicted by its own related work, and nothing rele |
| [2606.03115](https://arxiv.org/abs/2606.03115) | SPOQ: Specialist Orchestrated Queuing for Multi-Agent Software Engineering | [audit tightened admit_with_caveats->reject] Useful, concrete design (dependency-wave dispatch, pre/post gates, human planning review, failure-mode catalogue in |
| [2606.03394](https://arxiv.org/abs/2606.03394) | Human-AI Collaboration and the Transformation of Software Engineering Work | Position-style synthesis with a 12-source hand-curated corpus, no search protocol, single author coding, and no empirical validation of the framework or proposi |
| [2606.04397](https://arxiv.org/abs/2606.04397) | Context-as-AI-Service: Surfacing Cross-File Dependency Chains for LLM-Generated  | The efficiency numbers are the only measured, repeated result, and they do not show that documentation got more correct. The eight extra findings were selected  |
| [2606.05720](https://arxiv.org/abs/2606.05720) | Microskill Architecture: A Modular Skill-Driven Framework for AI-Native Code Gen | Evidence is a single unreplicated 15-feature case study with one model, a full-dump strawman baseline, no variance or ablations, a circular violations metric, u |
| [2606.07866](https://arxiv.org/abs/2606.07866) | Overcoming the Regulatory Bottleneck via Agent-to-Agent Protocols: A Nuclear Cas | off-topic: nuclear regulatory inter-organizational agent protocol, not software engineering or coding-agent harnesses; additionally, the quantitative claims are |
| [2606.09956](https://arxiv.org/abs/2606.09956) | Multi-task LLMs for Bug Classification: Efficient Inference with Auxiliary Decod | The task is line ranking inside a file the model is already given, and the headline Defects4J number is the maximum of a sweep whose mean is 16.9% Top-5. The ag |
| [2606.12425](https://arxiv.org/abs/2606.12425) | An Explainable AI Assistant for Introductory Programming Education: Improving Fe | [audit tightened admit_with_caveats->reject] There is a real, double-coded comparison in which canned instructor feedback invents fewer issues than GPT-4o, and  |
| [2606.13175](https://arxiv.org/abs/2606.13175) | The End of Code Review: Coding Agents Supersede Human Inspection | Provocative, well-structured position from an established SE researcher that is useful for framing merge-gate design, but its central claims are unsupported by  |
| [2606.14066](https://arxiv.org/abs/2606.14066) | FastContext: Training Efficient Repository Explorer for Coding Agents | Withdrawn by the authors (v4). Nothing can be verified. |
| [2606.14790](https://arxiv.org/abs/2606.14790) | XFlow: An Executable Protocol Programming System for Reliable Multi-Agent Workfl | Admitted only as a design reference for executable workflow specs with typed state, commit policies and human gates. The evidence is not usable as it stands. Th |
| [2606.15074](https://arxiv.org/abs/2606.15074) | TriAdReview: Triangular Adversarial Review Architecture for Multi-Model Technica | The headline +10.1% comes from the generator grading its own revised documents; the only other judge is a system participant and finds no significant effect, an |
| [2606.15874](https://arxiv.org/abs/2606.15874) | LLM-as-Code: Agentic Programming for Agent Harness | A position paper whose single quantitative claim is an uncontrolled leaderboard comparison: baselines are not re-run, the step budget differs, a three-domain su |
| [2606.15943](https://arxiv.org/abs/2606.15943) | Graphical-Probabilistic Modeling of Generative Flows in LLM-Native Software Syst | Position/notation paper with no evaluation. It is about designing LLM-based applications, not about how developers or agents build software, so it is off-topic  |
| [2606.17203](https://arxiv.org/abs/2606.17203) | Trust-Aware Multi-Agent Traceability: Confidence-Calibrated Knowledge Graphs for | The property in the title (calibrated confidence) is never measured, and the abstract's 'ablations confirm calibration is essential' is not what the ablations t |
| [2606.18497](https://arxiv.org/abs/2606.18497) | Ghost Vectors: Soft-Deleted Embeddings Remain Reconstructible in HNSW Vector Dat | Off-topic: vector-database storage security and erasure compliance, not LLM agents, coding agents or harness design. The evidence is also mixed: clinical claims |
| [2606.19616](https://arxiv.org/abs/2606.19616) | Before the Pull Request: Mining Multi-Agent Coordination | No LLM agents or real repositories are evaluated. The headline 78%→0% result follows from the synthetic agents' policy, Tables 1 and 2 disagree on conflicting e |
| [2606.20173](https://arxiv.org/abs/2606.20173) | Qiskit Code Migration with LLMs | Small synthetic Python benchmark, single runs, inconsistent tables, and an abstract claim ('significantly reduces hallucinations') contradicted by its own discu |
| [2606.21151](https://arxiv.org/abs/2606.21151) | Context-Aware Generative AI for Automated Telecom Test Script Generation | A design sketch for graph-conditioned test updates, not evidence. The abstract's claims about effort, relevance and cycle time are withdrawn by the authors' own |
| [2606.22402](https://arxiv.org/abs/2606.22402) | Reinforcement learning to improve large language model-based automated code comp | Off-topic for this KB: domain-model fine-tuning for building-regulation compliance scripts, not software-development practice with agents. Methodologically, che |
| [2606.22756](https://arxiv.org/abs/2606.22756) | HERCULES: An Open-Source Simulation Framework for Heterogeneous Multi-Robot SLAM | Off-topic. This is a robot simulator and a SLAM and 3D-detection testbed, not software development with language models or the human side of it. On its own term |
| [2606.24937](https://arxiv.org/abs/2606.24937) | The Hitchhiker's Guide to Agentic AI: From Foundations to Systems | An unreviewed, LLM-assisted textbook with no empirical contribution and no systematic review method. It can serve as a background glossary, but none of its clai |
| [2606.27416](https://arxiv.org/abs/2606.27416) | Glite ARF: Verifier-Driven Research with Parallel LLM Coding Agents | A concrete, open-source design for parallel worktree agents with deterministic spec verifiers is directly reusable. The evidence is experience-report quality: n |
| [2606.28279](https://arxiv.org/abs/2606.28279) | Agentic Hardware Design as Repository-Level Code Evolution | The headline 100% is convergence against the scoring harness itself, with no hidden tests, no baselines, one model and one run, and a ChipBench task that fails  |
| [2606.28403](https://arxiv.org/abs/2606.28403) | Reinforcement Learning for Software Vulnerability Analysis: A Systematic Review  | off-topic: classic RL for C/C++ fuzzing and vulnerability detection, not LLM agents or agent harnesses. It is also a small, unreplicable search with a prose/tab |
| [2606.29437](https://arxiv.org/abs/2606.29437) | LLMography: Transforming Human-AI Conversations into Traceability, Oversight, an | There is no validated measurement. All KPIs are unvalidated LLM outputs on 19 conversations, with visible scoring inconsistencies, nothing is released, and the  |
| [2606.30689](https://arxiv.org/abs/2606.30689) | Citation Discipline in Spec-Driven Development: A Cross-Model Empirical Study of | [audit tightened admit_with_caveats->reject] One finding is defensible: requiring per-line requirement-ID comments changes the generated code and lowers run-to- |
| [2606.30704](https://arxiv.org/abs/2606.30704) | From Search to Synthesis: Training LLMs as Zero-Shot Workflow Generators | The headline claims are not supported by the body: 'single inference' is really best-of-20 with validation selection, 'remarkable zero-shot' has a mean below th |
| [2606.31551](https://arxiv.org/abs/2606.31551) | AutoTrainess: Teaching Language Models to Improve Language Models Autonomously | Off-topic. This is an agent harness for language-model post-training, not discovery, onboarding, codebase exploration, or developer learning. On its own terms t |
| [2606.31650](https://arxiv.org/abs/2606.31650) | ECHO: Prune To Act, Trace To Learn With Selective Turn Memory In Agentic RL | off-topic: an RL training recipe for long-horizon web-search agents. The team will not train policies, and the headline rests on 83 held-out items with a single |
| [2607.01640](https://arxiv.org/abs/2607.01640) | AgentFlow: Building Agent Dependency Graphs for Static Analysis of Agent Program | off-topic: analyzes the security/BOM of Python applications built on agent frameworks (LangChain, CrewAI, etc.), explicitly excluding coding agents like Claude  |
| [2607.05762](https://arxiv.org/abs/2607.05762) | Articulating Assumptions in AI-Generated Scientific Analyses through Task Decomp | off-topic: LLM code generation for collider-physics analyses, with evaluation of five hand-built task cards judged manually by the authors and no quantitative c |
| [2607.06101](https://arxiv.org/abs/2607.06101) | Agents That Teach: Towards Designing Incidental Learning Back into AI-Assisted S | No evaluation of any kind. The design principles and SHIELD are unvalidated, the only demonstration is one illustrative walkthrough, and the reported feedback i |
| [2607.06624](https://arxiv.org/abs/2607.06624) | AgentLens: Production-Assessed Trajectory Reviews for Coding Agent Evaluation | Useful, concrete design for trajectory-level and regression evaluation of Java coding agents (Maven/Gradle verifiers, pairwise CI regression checks), but the le |
| [2607.07881](https://arxiv.org/abs/2607.07881) | Functional and Secure Code Generation with Task Vectors | off-topic for the harness KB: a sound weight-steering method for <=7B open coding models on function-level Python/C completions; it requires access to model wei |
| [2607.10532](https://arxiv.org/abs/2607.10532) | Implicit Fine-tuning via Context Engineering: A Curriculum Learning Framework fo | off-topic: multimodal knowledge-graph entity alignment with staged prompting; not about LLM agents, coding harnesses, or software engineering. |
| [2607.10736](https://arxiv.org/abs/2607.10736) | Robo-Reporters: Evaluating Autonomous AI Agents as Algorithmic Gatekeepers in Co | off-topic: journalism research agents, not software engineering; and the headline multi-agent accuracy advantage is not statistically significant (p=.066), with |
| [2607.13041](https://arxiv.org/abs/2607.13041) | LessonBench-V1: A Benchmark Dataset for Evaluating AI Lesson Generation Agents | off-topic for the harness KB and no evaluation: a lesson-plan dataset built with LLMs and an unspecified human review; the proposed benchmark is never run. Not  |
| [2607.13339](https://arxiv.org/abs/2607.13339) | Not Your Usual Type(s): Data contracts as types across languages and engines | Vendor design write-up with zero quantitative evidence; useful as a pattern description (typed contracts at pipeline boundaries, fail-fast at three stages) but  |
| [2607.15593](https://arxiv.org/abs/2607.15593) | Scalable LLM Agent Tool Access in the Cloud | A real production systems paper with useful overhead measurements, including a negative one on stateful routing. Headline efficiency gains rest on an expose-all |
| [2607.15845](https://arxiv.org/abs/2607.15845) | Knowledge-Centric Agents for Workflow Generation in ComfyUI | Off-topic: this is generation of image-generation workflows (ComfyUI), not agentic coding harness design. It does not inform a reference team's choice betwee |
| [2607.15948](https://arxiv.org/abs/2607.15948) | TARS: A Theory-of-Mind Agent for Personalized In-IDE Code Comprehension | The body supports none of the three abstract claims. The speed-up is not significant, workload was never compared with the control, and personalisation was neve |
| [2607.16352](https://arxiv.org/abs/2607.16352) | Clarify Before Executing: A Self-Evolving Agent for Resolving Intent Asymmetry i | Off-topic for this KB. It concerns 3D asset-creation tools with simulated lay users, not software development with LLM agents or the developers using them. Even |
| [2607.16388](https://arxiv.org/abs/2607.16388) | Automated Hardware Validation Test Plan Generation for Large Scale AI Datacenter | Off-topic for this KB: hardware fault-injection test planning, not software development with agents. Its headline numbers also rest on test-case counts against  |
| [2607.17532](https://arxiv.org/abs/2607.17532) | CommitLLM: A Fine-Tuned Pipeline for Git Commit Message Generation | The headline quality claim compares judge scores from two different judge models, the compliance metric was rewritten post hoc to fit the pipeline's output shap |
| [2607.17686](https://arxiv.org/abs/2607.17686) | Integrating High-Level Requirements to Low-Level Tests with Machine-Readable V&V | A clear, released tool whose cost and scaling claims are measured and whose quality-checker limits are reported honestly. There is no evidence that it improves  |
| [2607.18356](https://arxiv.org/abs/2607.18356) | CODENS: Transforming Code Changes into Living, Accessible, and Queryable Documen | A design description with an 11-question, single-rater pilot and no baseline. Its comparative statements (agent mode most complete, operational advantages) are  |
| [2607.18555](https://arxiv.org/abs/2607.18555) | LM2Alloy: Investigating LLM-Generated Formal Specifications for Automated Test D | Interesting idea honestly framed as proof-of-concept, but evidence is one unconfirmed bug in one library, one model, Python only, and a weak baseline; the deter |
| [2607.18603](https://arxiv.org/abs/2607.18603) | AutoIndex: Learning Representation Programs for Retrieval | Off-topic: a retrieval-indexing optimization study on a general IR benchmark, not about software development with LLM agents or its human side. The method is re |
| [2607.19297](https://arxiv.org/abs/2607.19297) | Graph-Based Agentic AI with LangGraph: Workflow Pathways for Long-Running Statef | There is no evaluation; the authors say it is a recipe guide, not a benchmark. The decision heuristics are sensible but unmeasured, and benchmark results that a |
| [2607.20709](https://arxiv.org/abs/2607.20709) | NVIDIA-labs OO Agents: Native Python Object-Oriented Agents | Useful design ideas (typed validated termination, pass-by-reference code-as-action) and an informative harness feature survey, but benchmark wins are small, sin |
| [2607.21618](https://arxiv.org/abs/2607.21618) | LeafData: An Agentic System for Data Migration | No evaluation: three demos and design prose only, and the LLM's contribution is unspecified. It is also off-topic for the KB: a natural-language-to-configuratio |
| [2607.21859](https://arxiv.org/abs/2607.21859) | EviDAG: Auditable Causal DAG Authoring with Biomedical Literature | Off-topic for this KB. The 'DAG' is a causal graph for epidemiological analysis, not a task or workflow graph, and the system is a literature-curation tool, not |
| [2607.22406](https://arxiv.org/abs/2607.22406) | Vibe Coding: An Experiment with Test-Driven Development | One toy Python task, 16 participants, and a model-generation confound (GPT-3.5 vs GPT-5/Sonnet 4) between arms mean the comparison cannot isolate the interactio |
| [2607.22463](https://arxiv.org/abs/2607.22463) | Beyond Perspectives: A Trio-Ethnography of Interpretation Evolution in LLM-Suppo | [audit tightened admit_with_caveats->reject] On-topic as an account of how two instructors revised their reading of student AI use after talking to one student, |
| [2607.22511](https://arxiv.org/abs/2607.22511) | CausalSmith: A Formally Grounded, Self-Improving Agentic Framework for Automated | off-topic: automated mathematical research in causal inference via Lean, not software engineering; the evaluation is also self-rated with no baselines. |
| [2607.22642](https://arxiv.org/abs/2607.22642) | CRAFT: Learn the Schema, Execute the Plan | Interesting design lesson (internalize stable schemas instead of stuffing prompts) with a seeded ablation, but evidence is relative-only, closed, judge-scored,  |
| [2607.22917](https://arxiv.org/abs/2607.22917) | Agent Team Work Zone: An Automated, Persistent Workspace for Long-Lived Claude C | Admit only as a design reference for a file-backed persistence pattern. It has no evaluation at all, and every benefit claim is unsupported by the authors' own  |
| [2607.23088](https://arxiv.org/abs/2607.23088) | Poster: Rethinking Security in LLM Code Generation through Real-World Risk Scena | [audit tightened admit_with_caveats->reject] On-topic and broad (8 models, 9 languages, paired prompts), and the direction agrees with prior work that under-spe |
| [2607.23537](https://arxiv.org/abs/2607.23537) | ObsDriveBench: Benchmarking Multimodal Understanding under Adverse Weather with  | Off-topic: an autonomous-driving vision-language benchmark under adverse weather, with no bearing on LLM coding agents, agent harnesses, or software engineering |
| [2607.24162](https://arxiv.org/abs/2607.24162) | Agent-UCT: Upper Confidence Bounds Applied to Trees for Agentic Workflow Optimiz | The central algorithmic contribution, cost-regularized UCT beating other search methods, is never tested: no competing optimizer, no lambda=0 ablation, one mode |
| [2607.25651](https://arxiv.org/abs/2607.25651) | Demystifying Deep Learning Compiler Frontend Bugs: An LLM-Aided Empirical Study | Off-topic for the harness KB: a root-cause taxonomy of PyTorch compiler-frontend bugs. The LLM-related claims (time savings, consistency, model-agnosticism, the |
| [2607.26348](https://arxiv.org/abs/2607.26348) | When Synthetic Users Fail: A Cross-Domain Benchmark of LLM-Simulated Human Surve | Off-topic for this KB. This is a careful survey-simulation benchmark with strong baselines and CIs, but it does not concern software development, coding agents, |
| [2607.27938](https://arxiv.org/abs/2607.27938) | VizPilot: Automated Onboarding for SVG-based Composite Visualizations using Mult | Off-topic: onboarding readers to data visualizations, not developers to code or domains. Its evidence is also weak (n=16, ceiling accuracy, strawman text baseli |
| [2607.28271](https://arxiv.org/abs/2607.28271) | Agentic Method for Deterministic Validation of Legacy Code Migration | Architecturally instructive industrial pattern (deterministic oracle gating agent proposals, agent repairs the deterministic migrator) but evidence is three unr |
| [2607.29610](https://arxiv.org/abs/2607.29610) | Educating the Agentic Engineer: Curricula, Collaboration, and Continuous Learnin | Position paper with no implementation or evaluation. Its central mitigation claims are explicitly design hypotheses. It is useful as a structured list of compre |
| [2608.01001](https://arxiv.org/abs/2608.01001) | From AI Technical Debt to Agentic Technical Debt: A Systematic Mapping of Root C | Conceptual relabelling of the authors' prior AI technical-debt taxonomy with no primary evidence about agentic systems, no reported inter-rater agreement and no |
| [2608.01324](https://arxiv.org/abs/2608.01324) | G-ReAct: Graph-Guided Deep Search via Structure-State Co-Evolution | off-topic: open-web deep-search QA agent training, not coding agents or software engineering; additionally relies on unvalidated LLM judging and copied baseline |
| [2608.05227](https://arxiv.org/abs/2608.05227) | BioMedJImpact: A Comprehensive Dataset and LLM Pipeline for AI Engagement and Sc | Off-topic: a scientometric dataset about biomedical journals, with no software development, coding agents, developer knowledge, or requirements content. It is a |
| [2608.05716](https://arxiv.org/abs/2608.05716) | BlockPython: A Process-Aware Agent-Supported Platform for the Transition from Bl | No evaluation at all, unnamed models, and the domain is K-12 programming education rather than professional software development with agents. It reads as a syst |
| [2608.06112](https://arxiv.org/abs/2608.06112) | From Siloed Algorithms to Compliance-First Agentic Platforms: A Multi-Layered Ar | off-topic: hospital clinical AI platform architecture, not LLM coding agents or SE harnesses; additionally the evidence is synthetic or unverifiable, internally |
| [2608.08038](https://arxiv.org/abs/2608.08038) | Stateful Multi-Agent LLMs for Cross-View Interface Alignment in Automotive Model | The abstract's 0% RAG traceability figure is contradicted by the paper's own table (34%). The evidence is one scenario with no run count, no variance, unnamed m |
| [2608.10290](https://arxiv.org/abs/2608.10290) | Comprendia: AI-Augmented Code Comprehension | A tool demo whose only measurements are prompt sizes on six fixtures in one toy project. The quality rubric could not distinguish any mode from selection-only,  |
| [2608.12025](https://arxiv.org/abs/2608.12025) | From Safety Documentation to Safety Knowledge Support: An Evidence-Grounded LLM  | Position paper with a non-systematic review and an unexecuted evaluation plan; no evidence on any pattern. The proposed artifact schema is sensible but untested |
| [2608.12375](https://arxiv.org/abs/2608.12375) | Pipeline Denotational Design: Correct-by-Construction Data Pipelines at Zero Cos | No empirical evaluation: the paper's own comment and §8 state results are pending. Formal theorems rest on proof sketches and the author's own companion paper;  |
| [2608.13662](https://arxiv.org/abs/2608.13662) | Ontology-Grounded Project Memory for Coding Agents | Vendor-run evaluation of a proprietary engine with unreported per-class sample sizes, partly circular ground truth, a judge validated only against the system's  |
| [2608.14944](https://arxiv.org/abs/2608.14944) | SkillComposer: Learning Reusable Skills for Natural-Language Robot Programming | Off-topic: natural-language robot programming for non-programmers in simulation, not software development with LLM agents or its human side. The abstract's head |
| [2608.15016](https://arxiv.org/abs/2608.15016) | Hierarchical Agentic Incident Response with Digital-Twin-Validated Attack Infere | off-topic: network-security incident response with a fine-tuned LLM and digital twin, not LLM coding agents or software engineering harnesses; also under-specif |
| [2608.16618](https://arxiv.org/abs/2608.16618) | The Specification Paradox: Rethinking Requirements Engineering in the Age of AI | Pure opinion piece with no original evaluation; the named concepts are untested relabelings and the only numbers are borrowed from other studies. Useful as voca |
| [2608.20887](https://arxiv.org/abs/2608.20887) | KREL: Automatic Medical Coding via Knowledge-Guided Reasoning over Clinical Evid | Off-topic for this KB: clinical ICD coding with LLMs, not software development with LLM agents or its human side. Within its own field it is a reasonable peer-r |
| [2608.22551](https://arxiv.org/abs/2608.22551) | DAGSmith: Dependency-Aware Rewriting for dbt-Style SQL Pipelines | Off-topic for this KB. The paper is about cutting warehouse cost in SQL data pipelines; its 'DAG' is the dbt model graph being optimized, not an agent workflow  |
| [2608.23552](https://arxiv.org/abs/2608.23552) | Prime Agent: A Self-Improving RLM Harness | The headline ARC-AGI-3 number is unsupported in the body, the authors concede it does not isolate a harness effect, and the comparative table has no variance an |
| [2608.23610](https://arxiv.org/abs/2608.23610) | From Traceability to Justifiability: Accountability Structures in Agentic Softwa | Off-topic for this KB: release-provenance records for AI systems and CI/CD attestation, not software development with LLM agents or its human side. Its own thre |
| [2608.24913](https://arxiv.org/abs/2608.24913) | From Blind Edits to Verified Repair: Building Trustworthy User-Side LLM Agents f | Off-topic for this knowledge base: a user-side browser CSS-repair agent with small local models, not a software-engineering agent harness. The verified loop was |
| [2608.26171](https://arxiv.org/abs/2608.26171) | Mitigating Fabrication in Multi-Stage LLM Pipelines for Hiring: An Empirical Eva | Off-topic: an LLM hiring-content pipeline, not software engineering or agent harnesses. The study itself is carefully disclosed but rests on one human reviewer, |
| [2608.27790](https://arxiv.org/abs/2608.27790) | Credo: Reusable Declarative Primitives for Agentic Workflows | [audit tightened admit_with_caveats->reject] A clear idea with sensible checks (cost as well as accuracy in the round trip, explicit brief-only and searched ref |
| [2608.28421](https://arxiv.org/abs/2608.28421) | Program Learning with Verifiable Rewards: Symbolic Backpropagation for Post-Trai | The authors have discarded the paper's experiments because of errors in the benchmark and baseline numbers, so none of its quantitative claims can be used. It i |
| [2608.28726](https://arxiv.org/abs/2608.28726) | Pro-Router: Token-Aware Progressive Model Routing with Adaptive Edge-Cloud Colla | Off-topic: serving-layer routing for multimodal VQA with logit access to self-hosted models. It does not address coding agents or SE harnesses. Results also lac |
| [2608.30572](https://arxiv.org/abs/2608.30572) | Practical Implementation Report on Introducing Spec-Driven Development Using AI  | Peer-reviewed, honest threats-to-validity section, and on-topic (Java/Spring Boot, SDD with an explicit pre-plan investigation phase, comprehension checks). The |
| [2609.00252](https://arxiv.org/abs/2609.00252) | Spec-Driven Development for Agentic Software Engineering: Harnessing Human-Agent | No empirical evidence, mechanisms largely borrowed from Hassan et al. 2025 and a search method that doesn't match how the abstract describes it. Still, it is th |
| [2609.00365](https://arxiv.org/abs/2609.00365) | Dr. Claw: An AI Scientist Workspace for Vibe Research | The headline completeness gain rests on three tasks with one run each and a CI that includes zero. The gain comes entirely from elements the system's own skills |
| [2609.02149](https://arxiv.org/abs/2609.02149) | OmegaUse-SOP: SOP Engineering for Professional Computer Use from Human Demonstra | Off-topic: GUI automation of photovoltaic simulation software, not software development. The evaluation (5 tasks, best of 3, SOPs recorded and tuned on the test |
| [2609.03529](https://arxiv.org/abs/2609.03529) | KnowFeat: Knowledge-Guided Feature Engineering via LLM Agents | Off-topic for this KB: automated feature engineering for tabular ML, not software development or the developer's side of it. Within its own scope, the headline  |
| [2609.04208](https://arxiv.org/abs/2609.04208) | AI Writes Code, Humans Pay the Debt. An Empirical Study on the Sustainability an | The pre-registered design is sound and relevant: Java, real OSS history, Sonar-family metrics, and a Stage 1 ESEM acceptance. But there are no results, so it ca |
| [2609.05529](https://arxiv.org/abs/2609.05529) | DART: A DAG-Based Reputation and Incentive Framework via Blockchain-Enabled Gove | The headline numbers are selective (one winning benchmark out of four), the coordination claim rests on one run of one task with inconsistent timings, and the D |
| [2609.05667](https://arxiv.org/abs/2609.05667) | The Impact of GenAI on the Future of Requirements Engineering | Useful, well-hedged framing of spec-driven development and RE evaluation gaps, but it is an explicitly non-systematic narrative essay with no new evidence; any  |
| [2609.05692](https://arxiv.org/abs/2609.05692) | Regret Dominates Surprise: Design-Time Requirements Engineering for Agentic-AI S | Headline simulation result is tautological (baseline evaluated with its signal disabled), the AgentHarm proxy is post-hoc, uses benchmark category labels as gat |
| [2609.11127](https://arxiv.org/abs/2609.11127) | KuaiRP Series Role-playing Models Technical Report | Off-topic (game role-play model training, not software development). It is also a vendor self-evaluation on a closed in-house benchmark, and its key CDD claim i |
| [2609.19199](https://arxiv.org/abs/2609.19199) | Code-as-Auditor: Executable Compliance Reasoning via Regulation-to-Code | Off-topic: LLM legal-compliance reasoning over regulation text, not software development with agents or its human side. On its own terms, the gains rest on auth |
| [2609.20063](https://arxiv.org/abs/2609.20063) | Robust Workflow Generation via Adversarial Learning for Audio Deepfake Detection | Off-topic for coding-agent harnesses: the subject is audio deepfake detection. Beyond relevance, the abstract's 'consistently outperforms' claim is contradicted |
| [2609.20143](https://arxiv.org/abs/2609.20143) | Designing Against Deskilling: Metacognitive Feedback Reduces Cognitive Offloadin | Off-topic under the KB scope. This is a well-run, preregistered, adequately powered RCT, but it studies fraction-arithmetic practice by general-population adult |
| [2609.21254](https://arxiv.org/abs/2609.21254) | Two's a Crowd: Human and AI-Based Copresence for Developers with ADHD | off-topic: a qualitative accessibility study of ADHD developers' copresence practices; methodologically reasonable for its genre but says nothing testable about |
| [2609.22196](https://arxiv.org/abs/2609.22196) | EvoRank: LLM-Guided Evolution of Multi-Objective Learning-to-Rank Pipelines | Off-topic. This is an LLM-guided AutoML search over learning-to-rank pipelines for hotel search, not software development with agents or its human side. The stu |
| [2609.22254](https://arxiv.org/abs/2609.22254) | Teacher Should Think Ahead: Adaptive Continuations for Reliable On-Policy Distil | off-topic: a method for distilling LLM weights on math and Python function-level benchmarks, with nothing about agents, harnesses or software-engineering workfl |
| [2609.24348](https://arxiv.org/abs/2609.24348) | A Lean and Spec-Driven AI-Assisted Software Development Lifecycle for Applied AI | Useful as a concrete, released template for spec-driven development with AGENTS.md plus skills, but the evaluation is a 13-student perception survey with no con |
| [2609.24362](https://arxiv.org/abs/2609.24362) | VLM-in-Sandbox: Visual Workspaces for Agentic Visual Reasoning | off-topic: a visual-reasoning sandbox for VLMs on image QA and math benchmarks, with no software-engineering or code-agent tasks. The evaluation is reasonable,  |
| [2609.28520](https://arxiv.org/abs/2609.28520) | Certified Task-Conditioned Active Observability | off-topic: theoretical active-observability/control paper on finite Boolean systems with no LLM, agent harness, or software-engineering content. |
| [2609.28557](https://arxiv.org/abs/2609.28557) | BaseCamp --- An Agentic AI Framework for Automating DNA Sequencing Data Pipeline | Evaluation is not real: Tables 2-5 and Figures 8, 10, 11 are explicitly captioned as placeholders 'pending measurement', so every quantitative claim in the abst |
| [2609.29995](https://arxiv.org/abs/2609.29995) | Guardrails or Roadblocks? Effects of Pedagogical Style and Context Awareness in  | off-topic: classroom RCT on AI teaching-assistant prompt design for CS1 students, not LLM agents for software engineering or harness design; also omnibus-only s |
| [2609.33791](https://arxiv.org/abs/2609.33791) | Do We Really Need KL Divergence for On-Policy Distillation of Large Language Mod | off-topic: LLM distillation loss study evaluated on math and Python function-level code benchmarks; it does not concern agents, harnesses, or repository-scale s |
| [2609.36783](https://arxiv.org/abs/2609.36783) | A Heckler in the Hidden State: Correctness Signals in Diffusion Language Models | Off-topic: this is model-internals interpretability of diffusion language models on Python function puzzles, not software-development practice, codebase discove |
| [2609.39383](https://arxiv.org/abs/2609.39383) | From Search to Signal: Online Post-Training in Automatic Heuristic Design | Off-topic for this KB: it studies RL reward construction for evolving TSP/CVRP heuristics, not software development with LLM agents or developer knowledge disco |
| [2610.00555](https://arxiv.org/abs/2610.00555) | Extending LLM-based support for software engineers with ADHD | The evaluation is perception of a demo video by mostly non-target respondents plus one end user, with no baseline and no outcome measures. The abstract's headli |
| [2610.01471](https://arxiv.org/abs/2610.01471) | When Does a Second Model Help? Cross-Model Review in LLM Verification | The paper is unusually candid and its statistics are cautious. But each headline comparison has an unresolved confound that could produce the observed differenc |
| [2610.02456](https://arxiv.org/abs/2610.02456) | SideKernel: A Usable microVM Sandbox for AI Coding Agents on macOS | A candid practicum report with a thorough threats-to-validity section, but the evidence is an informal survey plus single-evaluator binary tests of the author's |
| [2610.02877](https://arxiv.org/abs/2610.02877) | Evaluating LLM-as-a-Judge Beyond Score Alignment: A Psychometric Analysis of Res | off-topic: a psychometric analysis of small LLM judges on news-summary quality (SummEval). It is not about LLM agents, coding or software engineering. Methodolo |
| [2610.05860](https://arxiv.org/abs/2610.05860) | Curriculum Brain: Constructing Curriculum Knowledge Graphs as a Substrate for Co | Off-topic for this knowledge base: it is an LLM pipeline that builds a curriculum knowledge graph, not software development with agents or the developer side of |
| [2610.06829](https://arxiv.org/abs/2610.06829) | CLIFT: Conformal Self-Verification for Web Agent Training and Test-Time Scaling | off-topic: RL training and test-time selection for browser web agents, not software engineering harnesses; additionally SOTA claims rest on compute-mismatched c |
| [2610.07446](https://arxiv.org/abs/2610.07446) | CogAdapt: Cognition-informed Sparse Adaptation of Code LLMs | [audit tightened admit_with_caveats->reject] A reasonable ablation design on two MoE models, but every number is one generation pass on small test sets, the unt |
| [2610.07787](https://arxiv.org/abs/2610.07787) | OOPMAS: Object-Oriented Multi-Agent Systems for Query-Level Workflow Generation | The headline comparison is confounded by design. OOPMAS optimises each workflow against the ground-truth scorer of the very query it reports, while baselines do |
| [2610.09901](https://arxiv.org/abs/2610.09901) | A Chat Assistant for Software Exploration in a 3D Software Visualization | On-topic for codebase comprehension and exploration, but the evidence is a perception-only usability pilot. It has 11 mostly-student participants, some tied to  |
| [2610.10226](https://arxiv.org/abs/2610.10226) | Why Software Engineering Is Indispensable in the Age of Coding Agents | A well-written viewpoint with no new evidence. Its central claim (a training-proof 'structural vacuum') is asserted and unfalsifiable, its empirical section is  |

## Second-opinion audits

| Agreement | Papers |
| --- | --- |
| minor_disagreement | 104 |
| agree | 54 |
| partial | 53 |
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
