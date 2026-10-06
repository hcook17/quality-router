# Generated KB tables

Regenerate with `python3 etl.py load && python3 etl.py report`.

Harvested unique papers: 5585. Reviews by gate status: {'admitted': 7, 'caveated': 150, 'rejected': 71}.

## Pattern evidence matrix

Weighted score = sum of review weights (rigor x reproducibility x COI discount; caveated x0.6; rejected 0).

| Pattern | Supports | Contradicts | Mixed | Introduces | Weighted support | Weighted contra | Vendor-authored share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P01 Hierarchical repo instruction files (AGENTS.md/CLAUDE.md) | 0 | 2 | 5 | 2 | 0.00 | 1.00 | 0% |
| P02 Progressive disclosure / skills loaded on demand | 6 | 1 | 8 | 7 | 2.25 | 0.24 | 19% |
| P03 Deferred tool loading / small tool catalog | 4 | 0 | 0 | 2 | 1.62 | 0.00 | 12% |
| P04 MCP as integration layer | 4 | 1 | 3 | 2 | 1.03 | 0.20 | 17% |
| P05 Lexical/deterministic code retrieval (grep, AST, LSP) | 13 | 0 | 8 | 2 | 4.32 | 0.00 | 8% |
| P06 Embedding/RAG retrieval over code | 4 | 3 | 8 | 2 | 1.60 | 0.37 | 15% |
| P07 Code/knowledge graph context | 8 | 1 | 0 | 6 | 2.33 | 0.24 | 7% |
| P08 Context compaction / summarization | 10 | 5 | 6 | 2 | 2.37 | 1.32 | 7% |
| P09 Persistent agent memory | 5 | 1 | 2 | 5 | 1.77 | 0.30 | 17% |
| P10 Single-agent linear loop | 4 | 2 | 1 | 0 | 0.98 | 0.75 | 0% |
| P11 Multi-agent / role-based teams | 4 | 2 | 7 | 12 | 1.53 | 0.58 | 18% |
| P12 Subagents for isolated exploration | 5 | 1 | 4 | 2 | 1.58 | 0.21 | 13% |
| P13 Planner-executor / hierarchical orchestration | 6 | 1 | 8 | 5 | 2.04 | 0.24 | 8% |
| P14 Spec-driven / spec-first development | 6 | 0 | 5 | 10 | 1.84 | 0.00 | 13% |
| P15 Test-first / TDD with agents | 3 | 2 | 4 | 1 | 0.86 | 0.66 | 6% |
| P16 Execution-based verifier loop (tests/compile) | 35 | 2 | 13 | 7 | 9.04 | 0.42 | 15% |
| P17 Static analysis / linter feedback in loop | 11 | 1 | 2 | 6 | 4.82 | 0.24 | 12% |
| P18 LLM-as-judge / AI reviewer | 6 | 7 | 22 | 9 | 1.66 | 1.64 | 11% |
| P19 Human approval gates | 5 | 2 | 4 | 7 | 1.13 | 0.53 | 11% |
| P20 OS/container sandboxing | 5 | 0 | 0 | 2 | 1.41 | 0.00 | 14% |
| P21 Policy-as-code permissions / guardrails | 9 | 2 | 2 | 10 | 4.00 | 0.27 | 11% |
| P22 Prompt-injection defenses | 2 | 1 | 2 | 1 | 0.16 | 0.33 | 0% |
| P23 Model routing / cascades | 8 | 1 | 1 | 4 | 2.56 | 0.29 | 8% |
| P24 Token/cost budgets and caps | 23 | 1 | 3 | 3 | 6.84 | 0.16 | 11% |
| P25 RL / fine-tuning of agent models | 17 | 1 | 1 | 3 | 2.55 | 0.33 | 10% |
| P26 Self-improving / searched harness | 2 | 3 | 2 | 4 | 0.67 | 0.41 | 15% |
| P27 Cross-repo coordination / contracts | 6 | 0 | 0 | 3 | 2.13 | 0.00 | 7% |
| P28 Deterministic codemods / recipe-based migration | 5 | 0 | 2 | 1 | 1.55 | 0.00 | 25% |
| P29 Parallel agents with isolated worktrees | 3 | 0 | 2 | 3 | 0.66 | 0.00 | 27% |
| P30 Observability / tracing / audit | 11 | 0 | 0 | 18 | 3.98 | 0.00 | 22% |
| P31 Benchmark-based evaluation (SWE-bench family) | 1 | 1 | 5 | 16 | 5.14 | 0.33 | 10% |
| P32 Field/industrial evaluation | 9 | 0 | 1 | 1 | 3.17 | 0.00 | 7% |
| P33 CodeAct / code-as-action / CLI-first tools | 8 | 2 | 2 | 1 | 1.76 | 0.54 | 20% |
| P34 Structured requirements / acceptance criteria | 15 | 0 | 5 | 10 | 4.25 | 0.00 | 9% |
| P35 Formal methods / verified generation | 8 | 0 | 1 | 3 | 1.79 | 0.00 | 7% |

## Bias frequency

| Bias | Papers |
| --- | --- |
| no_variance_reported | 114 |
| small_sample | 104 |
| self_evaluation | 101 |
| metric_mismatch | 99 |
| closed_artifacts | 74 |
| hype_language | 63 |
| single_model | 56 |
| contamination_risk | 55 |
| strawman_baseline | 52 |
| llm_judge_unvalidated | 52 |
| toy_tasks | 46 |
| single_language_python | 38 |
| selection_bias_participants | 34 |
| cherry_picked_examples | 30 |
| missing_cost_reporting | 27 |
| self_reported_numbers | 24 |
| novelty_inflation | 18 |
| other:internal_inconsistency | 13 |
| survivorship | 12 |
| benchmark_overfit | 11 |
| other:off_topic | 7 |
| other:no_evaluation | 5 |
| other:no_limitations_section | 4 |
| other:abstract_body_mismatch | 4 |
| other:single_harness | 2 |

## COI severity

| Severity | Papers | Mean rigor |
| --- | --- | --- |
| high | 8 | 1.75 |
| low | 82 | 2.45 |
| medium | 15 | 1.80 |
| none | 123 | 2.47 |

## Contribution types

| Type | Papers | Mean rigor | Rejected |
| --- | --- | --- | --- |
| empirical | 87 | 2.69 | 20 |
| system | 68 | 2.29 | 22 |
| benchmark | 27 | 2.85 | 2 |
| position | 14 | 0.93 | 13 |
| tool | 10 | 2.00 | 4 |
| survey | 9 | 1.89 | 4 |
| theory | 7 | 2.00 | 4 |
| dataset | 5 | 2.40 | 2 |
| replication | 1 | 3.00 | 0 |

## Topic coverage

| Topic | Harvested (pass gate) | Reviewed | Admitted+caveated |
| --- | --- | --- | --- |
| T01 Agent harness engineering | 200 | 4 | 4 |
| T02 Coding agent architecture | 200 | 4 | 4 |
| T03 Agent loop and control flow | 173 | 4 | 1 |
| T04 Self-improving / meta-harness | 72 | 4 | 3 |
| T05 Long-horizon autonomous coding | 165 | 4 | 4 |
| T06 Repository instruction files (AGENTS.md) | 23 | 4 | 3 |
| T07 Context engineering | 67 | 4 | 2 |
| T08 Context compaction and summarization | 63 | 4 | 4 |
| T09 Agent memory | 196 | 4 | 3 |
| T10 Skills and procedural knowledge | 200 | 4 | 4 |
| T11 Repository-level code retrieval | 178 | 4 | 4 |
| T12 Model Context Protocol | 193 | 4 | 3 |
| T13 Tool selection and catalog scale | 117 | 4 | 4 |
| T14 LSP and semantic code tools | 5 | 4 | 4 |
| T15 Code graphs and knowledge graphs | 18 | 4 | 4 |
| T16 CLI vs tool-calling vs CodeAct | 13 | 4 | 3 |
| T17 Multi-agent software engineering | 27 | 4 | 4 |
| T18 Subagents and delegation | 144 | 4 | 3 |
| T19 Orchestrator-worker and planners | 70 | 4 | 0 |
| T20 Parallel agents and merge conflicts | 20 | 4 | 2 |
| T21 Agent communication protocols | 13 | 4 | 2 |
| T22 Spec-driven development | 32 | 4 | 2 |
| T23 Requirements engineering with LLMs | 59 | 4 | 1 |
| T24 Formal specs and verification-aware generation | 59 | 4 | 3 |
| T25 Agent planning for software tasks | 70 | 4 | 3 |
| T26 Design docs and architecture by agents | 2 | 2 | 1 |
| T27 Test generation by agents | 103 | 4 | 4 |
| T28 Test-driven development with agents | 17 | 4 | 3 |
| T29 Verifier and feedback loops | 138 | 4 | 3 |
| T30 Static analysis feedback to agents | 143 | 4 | 2 |
| T31 AI code review | 83 | 4 | 2 |
| T32 LLM-as-judge reliability | 200 | 4 | 3 |
| T33 Multi-repository and cross-repo changes | 59 | 5 | 3 |
| T34 API contracts and breaking changes | 10 | 4 | 4 |
| T35 Code migration and refactoring at scale | 7 | 4 | 2 |
| T36 Dependency and build repair | 7 | 4 | 4 |
| T37 Issue-to-PR autonomy in industry | 49 | 4 | 4 |
| T38 Agent sandboxing and isolation | 165 | 4 | 2 |
| T39 Prompt injection in coding agents | 192 | 4 | 3 |
| T40 Security of agent-generated code | 12 | 4 | 3 |
| T41 Permissions, policy and guardrails | 175 | 4 | 2 |
| T42 Supply chain: skills, plugins, MCP | 105 | 4 | 1 |
| T43 Agent observability and audit | 121 | 4 | 2 |
| T44 SWE benchmark validity and contamination | 157 | 4 | 4 |
| T45 Agent evaluation methodology | 120 | 4 | 3 |
| T46 Developer productivity field studies | 28 | 4 | 3 |
| T47 Adoption and human-AI collaboration in teams | 48 | 4 | 3 |
| T48 Maintainability of agent-written code | 26 | 4 | 1 |
| T49 Model routing and cascades | 45 | 4 | 3 |
| T50 Token cost and efficiency of agents | 68 | 4 | 4 |
| T51 RL training of software agents | 59 | 4 | 3 |
| T52 Small models and distillation for agents | 56 | 4 | 1 |
| T53 Java and JVM with LLMs | 126 | 4 | 4 |
| T54 Data pipelines and ETL agents | 73 | 4 | 1 |
| T55 Schema evolution and data contracts | 5 | 4 | 2 |
| T56 Healthcare software and compliance with LLMs | 7 | 4 | 2 |
| T57 Educational content generation and quality | 2 | 2 | 0 |
| T58 Accessibility conformance with LLMs | 45 | 4 | 2 |

## Top-weighted admitted papers

| arXiv | Title | Type | Rigor | COI | Weight |
| --- | --- | --- | --- | --- | --- |
| [2606.13298](https://arxiv.org/abs/2606.13298) | Mining Architectural Quality Under Agentic AI Adoption: A Causal Study of Java Repositorie | empirical | 4 | none | 0.8 |
| [2605.27787](https://arxiv.org/abs/2605.27787) | Long Live the Librarian! A Persistent Search Sub-Agent for Energy-Efficient Multi-Agent So | empirical | 4 | none | 0.736 |
| [2605.26156](https://arxiv.org/abs/2605.26156) | Turning Bias into Bugs: Bandit-Guided Style Manipulation Attacks on LLM Judges | empirical | 4 | none | 0.736 |
| [2608.30497](https://arxiv.org/abs/2608.30497) | Bridge: Automatically Mining Ecosystem-Scale API Update Mappings and Client Update Instanc | dataset | 4 | none | 0.736 |
| [2608.23550](https://arxiv.org/abs/2608.23550) | When "Do Not" Is Not Deny: Security Rules in CLAUDE.md vs Built-In Controls | empirical | 4 | none | 0.672 |
| [2605.15569](https://arxiv.org/abs/2605.15569) | Detecting Privilege Escalation in Polyglot Microservices via Agentic Program Analysis | system | 4 | low | 0.648 |
| [2606.22263](https://arxiv.org/abs/2606.22263) | Revelio: Cost-Efficient Agentic Memory Safety Vulnerability Detection For Repository-Scale | system | 3 | low | 0.486 |
| [2605.06445](https://arxiv.org/abs/2605.06445) | Constraint Decay: The Fragility of LLM Agents in Backend Code Generation | empirical | 4 | none | 0.442 |
| [2605.17242](https://arxiv.org/abs/2605.17242) | From Runnable to Shippable: Multi-Agent Test-Driven Development for Generating Full-Stack  | empirical | 4 | none | 0.442 |
| [2608.25939](https://arxiv.org/abs/2608.25939) | XREPOTEST: Benchmarking Multilingual Repository-Level Unit Test Generation for Large Langu | benchmark | 4 | none | 0.442 |
| [2608.06848](https://arxiv.org/abs/2608.06848) | Understanding and Improving Model Editing for Secure Code Generation | empirical | 4 | none | 0.442 |
| [2606.12344](https://arxiv.org/abs/2606.12344) | Claw-SWE-Bench: A Benchmark for Evaluating OpenClaw-style Agent Harnesses on Coding Tasks | benchmark | 4 | low | 0.389 |
| [2609.33762](https://arxiv.org/abs/2609.33762) | EfficientAgent: What Makes KV Cache Offloading Work for Concurrent Agents? | system | 4 | low | 0.389 |
| [2607.25431](https://arxiv.org/abs/2607.25431) | CodeNib: A Multi-View Data System for Serving Repository Context to Coding Agents | system | 4 | none | 0.365 |
| [2607.02825](https://arxiv.org/abs/2607.02825) | JavaVulBench: A Java Vulnerability Benchmark with Realistic Splits, a Unified Multi-Backen | benchmark | 3 | none | 0.36 |
| [2606.24446](https://arxiv.org/abs/2606.24446) | Agentic Generation of AST Transformation Rules for Fixing Breaking Updates | empirical | 3 | none | 0.331 |
| [2607.03691](https://arxiv.org/abs/2607.03691) | Don't Blame the Large Language Model: How Agent Harness Evolution Shapes Coding Agent Qual | empirical | 3 | none | 0.331 |
| [2607.18057](https://arxiv.org/abs/2607.18057) | Test Coverage Analysis of Agentic Pull Requests | empirical | 3 | none | 0.331 |
| [2608.09072](https://arxiv.org/abs/2608.09072) | A Unified Issue Resolution Benchmark for Requirement Clarification, Planning, and Code Gen | benchmark | 3 | none | 0.331 |
| [2606.18168](https://arxiv.org/abs/2606.18168) | All Smoke, No Alarm: Oracle Signals in Agent-Authored Test Code | empirical | 3 | none | 0.331 |
| [2607.22585](https://arxiv.org/abs/2607.22585) | The Scaffold Effect in Coding Agents: Harness Choice as a Hidden Variable in Coding-Agent  | empirical | 3 | none | 0.331 |
| [2607.27250](https://arxiv.org/abs/2607.27250) | Do Context Files Help Coding Agents? A Two-Agent Ablation Study on Real Repositories | empirical | 3 | none | 0.331 |
| [2608.08453](https://arxiv.org/abs/2608.08453) | What Keeps Agent Skills from Being Reusable? Evidence from 138K SKILL.md Files | empirical | 3 | none | 0.331 |
| [2606.01629](https://arxiv.org/abs/2606.01629) | Benchmarking LLM-as-a-Judge for Long-Form Output Evaluation | benchmark | 3 | none | 0.331 |
| [2606.25195](https://arxiv.org/abs/2606.25195) | SoK: AI Secure Code Generation: Progress, Pitfalls, and Paths Forward | survey | 3 | none | 0.331 |
| [2606.31174](https://arxiv.org/abs/2606.31174) | ClawArena-Team: Benchmarking Subagent Orchestration and Dynamic Workflows in Language-Mode | benchmark | 3 | none | 0.331 |
| [2606.31767](https://arxiv.org/abs/2606.31767) | JETO-Bench: A Reproducible Benchmark for Execution Time Improvement Patches in Java | benchmark | 3 | none | 0.331 |
| [2607.07980](https://arxiv.org/abs/2607.07980) | 3100 Opinions on Code Review in an AI World: Building Causal Theory from Practitioner Disc | theory | 3 | none | 0.331 |
| [2607.26375](https://arxiv.org/abs/2607.26375) | (Im)Paired Programming: Coding Agents Improve Productivity but Harm Understanding | empirical | 3 | none | 0.331 |
| [2608.06477](https://arxiv.org/abs/2608.06477) | StepJack: Benchmarking Computer-Use Agent Safety Against Multi-Step Indirect Prompt Inject | benchmark | 3 | none | 0.331 |
| [2608.09802](https://arxiv.org/abs/2608.09802) | SWE-Bench ProMax: Benchmarking Agents on Large-Scale Multilingual Code Refactoring | benchmark | 3 | none | 0.331 |
| [2608.25457](https://arxiv.org/abs/2608.25457) | MACGen: Toward Functionally Correct and Secure Code Generation via Multi-Agent Collaborati | system | 3 | none | 0.331 |
| [2609.00362](https://arxiv.org/abs/2609.00362) | Revisiting Feedback-Driven LLM Code Repair: A Replication and Exploratory Java Extension | replication | 3 | none | 0.331 |
| [2609.08318](https://arxiv.org/abs/2609.08318) | AttnCompress: Dynamic Attention-Guided Trajectory Compression for Software Engineering Age | system | 3 | none | 0.331 |
| [2609.22222](https://arxiv.org/abs/2609.22222) | Can Coding Agents Reproduce Official Statistics? Metadata, Retry Budget and the Limits of  | empirical | 3 | none | 0.331 |
| [2605.29737](https://arxiv.org/abs/2605.29737) | Minimal Prompt Perturbations Lead to Code Vulnerabilities: Prompt Fragility and Hidden-Sta | empirical | 3 | none | 0.331 |
| [2606.08500](https://arxiv.org/abs/2606.08500) | Projecting the Emerging Mindset of SWE Agent by Launching a Wild Code Understanding Journe | empirical | 3 | none | 0.331 |
| [2606.21926](https://arxiv.org/abs/2606.21926) | A11YRepair: Bridging Web Accessibility Barriers via Knowledge-Enhanced Divide-and-Conquer  | system | 3 | none | 0.331 |
| [2607.21832](https://arxiv.org/abs/2607.21832) | How Do AI Coding Agents Contribute to Software Development? an Empirical Study of Agentic  | empirical | 3 | none | 0.331 |
| [2608.19799](https://arxiv.org/abs/2608.19799) | SWE-bench Science: Can Coding Agents Resolve Engineering Tasks in Science? | benchmark | 3 | none | 0.331 |

## Rejected

| arXiv | Title | Reason |
| --- | --- | --- |
| [2605.01533](https://arxiv.org/abs/2605.01533) | Genetic Programming for Self-Adaptive Auto-Scaling of Microservices | off-topic: runtime microservice auto-scaling with genetic programming. No LLM agents, coding harness, or SE-automation content. The evaluation is reasonable for |
| [2605.04449](https://arxiv.org/abs/2605.04449) | GEM: Graph-Enhanced Mixture-of-Experts with ReAct Agents for Dialogue State Trac | off-topic: dialogue state tracking on MultiWOZ, not LLM coding agents or SE. The SOTA margin is small, single-run, and against quoted baselines, and the efficie |
| [2605.04902](https://arxiv.org/abs/2605.04902) | AegisTS: A Hierarchical Agentic AI System with Reinforcement Learning for Multiv | off-topic: RL-based time-series data cleaning. 'Agentic' refers to RL policies, not LLM coding agents. The headline numbers are best cases on synthetic corrupti |
| [2605.05584](https://arxiv.org/abs/2605.05584) | Operationalizing Ethics for AI Agents: How Developers Encode Values into Reposit | Position/vision paper with no evaluation: six cherry-picked excerpts and no test of whether agents follow the encoded values. It is useful only as a pointer to  |
| [2605.11868](https://arxiv.org/abs/2605.11868) | IPI-proxy: An Intercepting Proxy for Red-Teaming Web-Browsing AI Agents Against  | Design description of a red-teaming tool with no empirical evaluation; usable as a pointer to an artifact but provides no evidence for the knowledge base. |
| [2605.12652](https://arxiv.org/abs/2605.12652) | Multi-Rollout On-Policy Distillation via Peer Successes and Failures | off-topic: model post-training/distillation method for small open models; no bearing on agent harness design, and evaluation lacks seeds with config apparently  |
| [2605.12718](https://arxiv.org/abs/2605.12718) | CHAL: Council of Hierarchical Agentic Language | off-topic: multi-agent debate on philosophical/defeasible questions, not software engineering or coding-agent harnesses; evaluation uses only internal metrics w |
| [2605.15721](https://arxiv.org/abs/2605.15721) | Contexting as Recommendation: Evolutionary Collaborative Filtering for Context E | off-topic: per-instance prompt/context optimization evaluated only on NLP QA and fact-verification datasets with one model; no coding, agent, or harness evaluat |
| [2605.16821](https://arxiv.org/abs/2605.16821) | Multi-Paradigm Agent Interaction in Practice:A Systematic Analysis of Generator- | No real evaluation: one cherry-picked case study and five scenarios scored by the system's own LLM evaluator; headline abstract numbers are absent from or contr |
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
| [2606.03394](https://arxiv.org/abs/2606.03394) | Human-AI Collaboration and the Transformation of Software Engineering Work | Position-style synthesis with a 12-source hand-curated corpus, no search protocol, single author coding, and no empirical validation of the framework or proposi |
| [2606.05720](https://arxiv.org/abs/2606.05720) | Microskill Architecture: A Modular Skill-Driven Framework for AI-Native Code Gen | Evidence is a single unreplicated 15-feature case study with one model, a full-dump strawman baseline, no variance or ablations, a circular violations metric, u |
| [2606.07866](https://arxiv.org/abs/2606.07866) | Overcoming the Regulatory Bottleneck via Agent-to-Agent Protocols: A Nuclear Cas | off-topic: nuclear regulatory inter-organizational agent protocol, not software engineering or coding-agent harnesses; additionally, the quantitative claims are |
| [2606.13175](https://arxiv.org/abs/2606.13175) | The End of Code Review: Coding Agents Supersede Human Inspection | Provocative, well-structured position from an established SE researcher that is useful for framing merge-gate design, but its central claims are unsupported by  |
| [2606.18497](https://arxiv.org/abs/2606.18497) | Ghost Vectors: Soft-Deleted Embeddings Remain Reconstructible in HNSW Vector Dat | Off-topic: vector-database storage security and erasure compliance, not LLM agents, coding agents or harness design. The evidence is also mixed: clinical claims |
| [2606.19616](https://arxiv.org/abs/2606.19616) | Before the Pull Request: Mining Multi-Agent Coordination | No LLM agents or real repositories are evaluated. The headline 78%→0% result follows from the synthetic agents' policy, Tables 1 and 2 disagree on conflicting e |
| [2606.20173](https://arxiv.org/abs/2606.20173) | Qiskit Code Migration with LLMs | Small synthetic Python benchmark, single runs, inconsistent tables, and an abstract claim ('significantly reduces hallucinations') contradicted by its own discu |
| [2606.24937](https://arxiv.org/abs/2606.24937) | The Hitchhiker's Guide to Agentic AI: From Foundations to Systems | An unreviewed, LLM-assisted textbook with no empirical contribution and no systematic review method. It can serve as a background glossary, but none of its clai |
| [2606.27416](https://arxiv.org/abs/2606.27416) | Glite ARF: Verifier-Driven Research with Parallel LLM Coding Agents | A concrete, open-source design for parallel worktree agents with deterministic spec verifiers is directly reusable. The evidence is experience-report quality: n |
| [2606.28403](https://arxiv.org/abs/2606.28403) | Reinforcement Learning for Software Vulnerability Analysis: A Systematic Review  | off-topic: classic RL for C/C++ fuzzing and vulnerability detection, not LLM agents or agent harnesses. It is also a small, unreplicable search with a prose/tab |
| [2606.31650](https://arxiv.org/abs/2606.31650) | ECHO: Prune To Act, Trace To Learn With Selective Turn Memory In Agentic RL | off-topic: an RL training recipe for long-horizon web-search agents. The team will not train policies, and the headline rests on 83 held-out items with a single |
| [2607.01640](https://arxiv.org/abs/2607.01640) | AgentFlow: Building Agent Dependency Graphs for Static Analysis of Agent Program | off-topic: analyzes the security/BOM of Python applications built on agent frameworks (LangChain, CrewAI, etc.), explicitly excluding coding agents like Claude  |
| [2607.05762](https://arxiv.org/abs/2607.05762) | Articulating Assumptions in AI-Generated Scientific Analyses through Task Decomp | off-topic: LLM code generation for collider-physics analyses, with evaluation of five hand-built task cards judged manually by the authors and no quantitative c |
| [2607.06624](https://arxiv.org/abs/2607.06624) | AgentLens: Production-Assessed Trajectory Reviews for Coding Agent Evaluation | Useful, concrete design for trajectory-level and regression evaluation of Java coding agents (Maven/Gradle verifiers, pairwise CI regression checks), but the le |
| [2607.07881](https://arxiv.org/abs/2607.07881) | Functional and Secure Code Generation with Task Vectors | off-topic for the harness KB: a sound weight-steering method for <=7B open coding models on function-level Python/C completions; it requires access to model wei |
| [2607.10532](https://arxiv.org/abs/2607.10532) | Implicit Fine-tuning via Context Engineering: A Curriculum Learning Framework fo | off-topic: multimodal knowledge-graph entity alignment with staged prompting; not about LLM agents, coding harnesses, or software engineering. |
| [2607.10736](https://arxiv.org/abs/2607.10736) | Robo-Reporters: Evaluating Autonomous AI Agents as Algorithmic Gatekeepers in Co | off-topic: journalism research agents, not software engineering; and the headline multi-agent accuracy advantage is not statistically significant (p=.066), with |
| [2607.13041](https://arxiv.org/abs/2607.13041) | LessonBench-V1: A Benchmark Dataset for Evaluating AI Lesson Generation Agents | off-topic for the harness KB and no evaluation: a lesson-plan dataset built with LLMs and an unspecified human review; the proposed benchmark is never run. Not  |
| [2607.13339](https://arxiv.org/abs/2607.13339) | Not Your Usual Type(s): Data contracts as types across languages and engines | Vendor design write-up with zero quantitative evidence; useful as a pattern description (typed contracts at pipeline boundaries, fail-fast at three stages) but  |
| [2607.18555](https://arxiv.org/abs/2607.18555) | LM2Alloy: Investigating LLM-Generated Formal Specifications for Automated Test D | Interesting idea honestly framed as proof-of-concept, but evidence is one unconfirmed bug in one library, one model, Python only, and a weak baseline; the deter |
| [2607.20709](https://arxiv.org/abs/2607.20709) | NVIDIA-labs OO Agents: Native Python Object-Oriented Agents | Useful design ideas (typed validated termination, pass-by-reference code-as-action) and an informative harness feature survey, but benchmark wins are small, sin |
| [2607.22406](https://arxiv.org/abs/2607.22406) | Vibe Coding: An Experiment with Test-Driven Development | One toy Python task, 16 participants, and a model-generation confound (GPT-3.5 vs GPT-5/Sonnet 4) between arms mean the comparison cannot isolate the interactio |
| [2607.22511](https://arxiv.org/abs/2607.22511) | CausalSmith: A Formally Grounded, Self-Improving Agentic Framework for Automated | off-topic: automated mathematical research in causal inference via Lean, not software engineering; the evaluation is also self-rated with no baselines. |
| [2607.22642](https://arxiv.org/abs/2607.22642) | CRAFT: Learn the Schema, Execute the Plan | Interesting design lesson (internalize stable schemas instead of stuffing prompts) with a seeded ablation, but evidence is relative-only, closed, judge-scored,  |
| [2607.22917](https://arxiv.org/abs/2607.22917) | Agent Team Work Zone: An Automated, Persistent Workspace for Long-Lived Claude C | Admit only as a design reference for a file-backed persistence pattern. It has no evaluation at all, and every benefit claim is unsupported by the authors' own  |
| [2607.23537](https://arxiv.org/abs/2607.23537) | ObsDriveBench: Benchmarking Multimodal Understanding under Adverse Weather with  | Off-topic: an autonomous-driving vision-language benchmark under adverse weather, with no bearing on LLM coding agents, agent harnesses, or software engineering |
| [2607.28271](https://arxiv.org/abs/2607.28271) | Agentic Method for Deterministic Validation of Legacy Code Migration | Architecturally instructive industrial pattern (deterministic oracle gating agent proposals, agent repairs the deterministic migrator) but evidence is three unr |
| [2608.01001](https://arxiv.org/abs/2608.01001) | From AI Technical Debt to Agentic Technical Debt: A Systematic Mapping of Root C | Conceptual relabelling of the authors' prior AI technical-debt taxonomy with no primary evidence about agentic systems, no reported inter-rater agreement and no |
| [2608.01324](https://arxiv.org/abs/2608.01324) | G-ReAct: Graph-Guided Deep Search via Structure-State Co-Evolution | off-topic: open-web deep-search QA agent training, not coding agents or software engineering; additionally relies on unvalidated LLM judging and copied baseline |
| [2608.06112](https://arxiv.org/abs/2608.06112) | From Siloed Algorithms to Compliance-First Agentic Platforms: A Multi-Layered Ar | off-topic: hospital clinical AI platform architecture, not LLM coding agents or SE harnesses; additionally the evidence is synthetic or unverifiable, internally |
| [2608.12375](https://arxiv.org/abs/2608.12375) | Pipeline Denotational Design: Correct-by-Construction Data Pipelines at Zero Cos | No empirical evaluation: the paper's own comment and §8 state results are pending. Formal theorems rest on proof sketches and the author's own companion paper;  |
| [2608.15016](https://arxiv.org/abs/2608.15016) | Hierarchical Agentic Incident Response with Digital-Twin-Validated Attack Infere | off-topic: network-security incident response with a fine-tuned LLM and digital twin, not LLM coding agents or software engineering harnesses; also under-specif |
| [2608.16618](https://arxiv.org/abs/2608.16618) | The Specification Paradox: Rethinking Requirements Engineering in the Age of AI | Pure opinion piece with no original evaluation; the named concepts are untested relabelings and the only numbers are borrowed from other studies. Useful as voca |
| [2608.23552](https://arxiv.org/abs/2608.23552) | Prime Agent: A Self-Improving RLM Harness | The headline ARC-AGI-3 number is unsupported in the body, the authors concede it does not isolate a harness effect, and the comparative table has no variance an |
| [2608.24913](https://arxiv.org/abs/2608.24913) | From Blind Edits to Verified Repair: Building Trustworthy User-Side LLM Agents f | Off-topic for this knowledge base: a user-side browser CSS-repair agent with small local models, not a software-engineering agent harness. The verified loop was |
| [2608.26171](https://arxiv.org/abs/2608.26171) | Mitigating Fabrication in Multi-Stage LLM Pipelines for Hiring: An Empirical Eva | Off-topic: an LLM hiring-content pipeline, not software engineering or agent harnesses. The study itself is carefully disclosed but rests on one human reviewer, |
| [2608.28726](https://arxiv.org/abs/2608.28726) | Pro-Router: Token-Aware Progressive Model Routing with Adaptive Edge-Cloud Colla | Off-topic: serving-layer routing for multimodal VQA with logit access to self-hosted models. It does not address coding agents or SE harnesses. Results also lac |
| [2609.00252](https://arxiv.org/abs/2609.00252) | Spec-Driven Development for Agentic Software Engineering: Harnessing Human-Agent | No empirical evidence, mechanisms largely borrowed from Hassan et al. 2025 and a search method that doesn't match how the abstract describes it. Still, it is th |
| [2609.04208](https://arxiv.org/abs/2609.04208) | AI Writes Code, Humans Pay the Debt. An Empirical Study on the Sustainability an | The pre-registered design is sound and relevant: Java, real OSS history, Sonar-family metrics, and a Stage 1 ESEM acceptance. But there are no results, so it ca |
| [2609.05667](https://arxiv.org/abs/2609.05667) | The Impact of GenAI on the Future of Requirements Engineering | Useful, well-hedged framing of spec-driven development and RE evaluation gaps, but it is an explicitly non-systematic narrative essay with no new evidence; any  |
| [2609.05692](https://arxiv.org/abs/2609.05692) | Regret Dominates Surprise: Design-Time Requirements Engineering for Agentic-AI S | Headline simulation result is tautological (baseline evaluated with its signal disabled), the AgentHarm proxy is post-hoc, uses benchmark category labels as gat |
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

## Second-opinion audits

| Agreement | Papers |
| --- | --- |
