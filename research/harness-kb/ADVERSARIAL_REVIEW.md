# Adversarial review of the KB and of agent standards (as of 2026-09-30)

This review attacks the KB's own method, then checks the standards that
govern agent harnesses as of 30 September 2026. Its numbers come from
`kb_robustness.md`, `kb_tables.md` and the live recheck. Regenerate:
`python3 etl.py load && python3 etl.py report && python3 etl.py
robustness`. The DAG question has its own write-up in `dag.md`.

**Verdict.** The KB's direction holds: deterministic sensors and
policy-as-code, short executable specs, and keeping the LLM out of the
merge decision. Its confidence did not hold. Single LLM reviews
overstated support. Four "consensus" labels did not survive a full
blind audit. The base is thin on Java, and it could not see topics it
never searched for. Every fix below is committed and reproducible.

## 1. Single reviews overstated support

Before this pass, only 59 of 240 reviews (25%) had a blind second
opinion. Across all 138 audits now on file, the auditor changed 139 of
219 `supports` stances (63%): 63 to neutral, 47 to mixed and 29 to
introduces. The rate was nearly the same in both rounds: 73 of 116
(63%) in the first 59 audits, and 66 of 103 (64%) in the 79 new ones.
The usual reason was that the paper used the
pattern in every arm, or changed several things at once, so it could
not isolate the effect.

**Fix:** blind-audit every evidence paper. All 112 are now audited. The
merge is conservative: lowest score, strictest verdict and weakest
claim strength win.

| Pattern | Before: S/C/M, hand label | After full audit: S/C/M, rule label |
| --- | --- | --- |
| P16 Execution verifier loop | 21/1/10, consensus | 10/1/14, **conditional** |
| P05 Lexical code retrieval | 8/0/7, consensus | 3/0/7, **conditional** |
| P12 Subagents for exploration | 2/0/4, consensus | 1/0/5, **unresolved** |
| P35 Formal methods | 6/0/1, consensus | 2/0/2, **leaning** |
| P17 Static analysis in the loop | 7/1/2, consensus | 3/0/1, consensus |
| P13 Planner-executor | 6/0/3, consensus | 5/0/5, consensus (falls to conditional without its top paper) |
| P21 Policy-as-code | 7/0/2, consensus | 6/0/2, consensus |
| P24 Token budgets | 7/0/2, consensus | 4/0/2, consensus |
| P30 Observability | 5/0/0, consensus | 3/0/2, consensus |
| P34 Structured acceptance criteria | 4/0/4, consensus | 5/0/4, consensus |
| P03 Small tool catalog | 3/0/0, unlabelled | 0/0/0, **none** |
| P10 Single-agent loop | 3/0/2, unlabelled | 0/0/4, **unresolved** |

S/C/M counts evidence papers that support, contradict or are mixed.

**What it means for `qr`.** P16 falling to conditional is the change
that matters most, and it cuts in the direction the gates already
assume. The 14 mixed papers name the conditions an execution verifier
needs:
- tests written apart from the implementation (2607.05139, 2608.16742);
- coverage of the changed lines (2607.18057);
- strong oracles (2606.18168);
- feedback that beats a blind redraw at the same budget (2609.22222);
- readable JUnit output on Java (2609.00362).

`qr gate diff-coverage`, `test-oracles`, `acceptance` and the held-out
run in phase 6 check exactly those conditions. What weakens is the
claim that "tests pass" is a good verifier on its own.

## 2. Hand labels went beyond the counts

- **P12 overclaimed.** `FINDINGS.md` labelled it consensus at 2
  supporting papers while ignoring 4 mixed ones.
- **Proposals counted as support.** The weighted-support column in
  `kb_tables.md` adds `introduces` stances. P31 carries 3.77 of
  proposal-only weight, and P16 carries 1.39.

**Fix:**
- `pattern_label` in `etl.py` assigns labels by a fixed rule:
  consensus, conditional, contested, leaning, unresolved or none.
- `robustness` lists every hand label that the rule does not
  reproduce.
- `FINDINGS.md` now uses the rule's labels.
- `introduces` is excluded from the rule.

## 3. The harvest could not see whole topics

- **DAGs.** None of the 58 topics targeted DAG or workflow-graph
  orchestration. I scanned the 5,589 abstracts of the earlier harvest
  for DAG, directed acyclic, task graph, workflow graph, LangGraph,
  state machine, topological order and agentic workflow. 132 matched,
  and only 12 of those had been reviewed, all for other topics. The
  count depends on the term list. The KB could not answer the DAG
  question until T59–T61 and 8 supplementary picks were added: 38
  papers, of which 18 are evidence, 5 hypothesis, 1 no contribution and
  14 rejected (9 off-topic, relevance ≤ 1).
- **Cross-repo coordination (P27), the team's core problem.** It is
  "unstudied" on 5 reviewed papers out of 59 harvested for T33.
  "Unstudied" may partly mean "not reviewed deeply enough". This is the
  next topic to deepen.

## 4. The evidence is not about Java

- **Java:** 21 of 112 evidence papers mention Java at least 5 times. On
  that subset, P16 stays conditional and P32 consensus. Every other
  consensus pattern loses its label: P17 falls to leaning, P30 to
  unresolved, and P13, P21, P24, P25 and P34 to none.
- **SWE-bench:** 38 of 112 rely on it. Without them:
  - P17 and P25 fall to leaning, P30 to none, and P02 and P36 to
    unresolved;
  - P05 rises to consensus (3/0/2), because most of its mixed papers
    are SWE-bench studies.
- **Human participants:** 11 of 112. **Industrial settings:** 18 of 112.

## 5. Dates, and "as of September 2026"

- **Window:** 278 reviewed papers have v1 dates from 2026-05-02 to
  2026-10-06. None falls outside the window. One is withdrawn and
  rejected (2606.14066).
- **Revisions:** a live arXiv recheck of all 278 on 2026-10-07 found
  none revised since review.
- **The September 30 cutoff:** three evidence papers were first posted
  between 1 and 6 October (2610.02932, 2610.02952, 2610.07851).
  Dropping them changes one label, P28 (from unresolved to leaning), so
  the "as of September" picture matches the full window.
- **ID versus published date:** 363 of 5,926 harvested papers (6%) have
  a `published` month earlier than their ID month, never later. That is
  consistent with arXiv moderation holds. The window check uses
  `published`, which is the stricter of the two.

## 6. Pipeline defects found and fixed

- **Lost papers on re-run:** `transform` and `select` rebuilt their
  outputs from the topic harvest only. Re-running them would have
  silently dropped the 12 papers added by ID. Both now merge.
- **Second gate bypass:** a paper with no contribution file loaded as
  evidence. It now loads as `unassessed` with weight 0.
- **Ad hoc recheck:** the live date recheck was a one-off; it is now
  `etl.py recheck`.

## 7. What the audits cannot fix

- **One model family.** Reviewers and auditors are the same family of
  LLM, so blind audits remove variance but not shared blind spots.
  Agreement is lowest on relevance: 66 of 138 exact, mean −0.49.
  Agreement on rigor is 108 of 138.
- **Vote counting is not meta-analysis.** The weight formula is ad
  hoc. P13 falls to conditional without its top-weighted paper (Repo0).
- **The literature itself:**
  - no variance reported in 49% of papers;
  - self-evaluation in 46%;
  - metrics that don't measure the claim in 46%;
  - small samples in 46%;
  - mostly preprints, with no replications.
- **Number-matching not reproducible.** The earlier check of reviewers'
  cited numbers against the paper text (1.1% unmatched) was not
  committed as a script, and it was not rerun for the 38 new reviews.
  An independent pass over this review's own documents found 22 wrong
  or overstated numbers and framings, all corrected (section 9).

## 8. Citations that no longer hold

- **2607.15593 is now rejected.** After the merge it scores rigor 2
  with high COI, which the gate rejects. It had been cited for "about
  15 inlined tools still select well":
  - in `architecture-decisions.md` (the catalog-size rationale);
  - in `implementations.md` (adopting Gortex `facade-v1`);
  - in `FINDINGS.md`;
  - in the header of the `.gortex.yaml` that `qr init --graph gortex`
    stamps.

  The first three are corrected. The stamp header is fixed text under
  the phase-6 acceptance lock (AC-15). Changing it is a spec-owner
  change with a re-lock, so it is left for that review. P03 (small tool
  catalog) now has no evidence paper. The `AGENTS.md` cap of about
  10–15 tools stands as policy, not evidence.
- **2609.01861 is now hypothesis only.** Its P26 support did not
  survive the appendix, so its "graded predictions for harness changes"
  citation in `FINDINGS.md` is marked as a hypothesis.

## 9. Numbers corrected by an independent check

A separate agent recomputed every aggregate in this file, `dag.md` and
`FINDINGS.md` with its own SQL, and checked paper-level numbers against
the full texts. All aggregates matched. Several paper claims were
overstated, and three of them had been repeated in `qr`'s docs and
docstrings since phase 3:

| Claim as written | What the paper shows | Where it was used |
| --- | --- | --- |
| Direct invocation of the focal method fell from 98.9% to 27.6% (2608.25939) | On PHP only. Go, Rust and Julia held or rose; Ruby fell from 84.3 to 68.6 | `FINDINGS.md`, phase-3 evidence map (diff-coverage) |
| Catch-all try/catch was the largest single reason generated tests missed breaking changes (2608.20167) | 78% of the tests that missed never loaded the changed class. Of 80 sampled from the rest, a silent null-object fallback (37) and catch blocks (32) hid the break | `FINDINGS.md`, phase-3 evidence map (test-oracles) |
| A static API diff catches 95% of what LLM-written client tests catch (2608.20167) | 95.1% of the tests that detected a break failed with a runtime error (missing class or method). That is crash-type breakage, the class japicmp targets. japicmp itself was not run | `FINDINGS.md`, `implementations.md`, phase-3 evidence map, `contracts.py`, `api_compat.py`, and the problem statement of the locked phase-6 spec |

The gates still stand. Executed changed lines, value oracles and a
static API diff each target a measured failure, but the citations now
say what was measured.

The locked phase-6 spec (`docs/design/phase-6-api-compat-and-gortex.md`)
keeps the old 95% wording, and so does the `.gortex.yaml` header (section
8). Editing either breaks `qr gate acceptance` until the spec owner
re-locks, so both are listed for that review rather than changed here.

The other corrections were in this review's own new text:
- **ORCA:** its baseline did see the fault signature.
- **PopPy's 2.0–3.2×** compares graph frameworks with an
  auto-parallelizing compiler, not with plain concurrent code.
- **2605.26521's edges** are developer-declared, and were unwitnessed
  by generated tests rather than unused.
- **Off-topic rejects** in the DAG batch number 9, not 10.

## 10. Standards as of 30 September 2026

Sources were checked on 2026-10-06/07 against primary pages. Facts
marked (2nd) rest on secondary sources.

| Standard | Status on 2026-09-30 | What matters here |
| --- | --- | --- |
| MCP ([spec](https://modelcontextprotocol.io/specification/2026-07-28/changelog)) | Revision `2026-07-28`; previous `2025-11-25`. Hosted by the Agentic AI Foundation (AAIF, Linux Foundation) since 2025-12-09 | Stateless core: no `initialize`, no session ID. Tasks became an extension. Dynamic Client Registration is deprecated for Client ID Metadata Documents; clients must validate `iss` (RFC 9207). Roots, Sampling, Logging and HTTP+SSE are deprecated. The registry is still preview. Papers that measured stateful MCP describe a superseded protocol |
| A2A ([releases](https://github.com/a2aproject/A2A/releases)) | v1.0.1 (2026-05-28); joined AAIF 2026-08-17 | Agent Card signing is optional ("MAY"); session smuggling and card poisoning are reported. KB evidence: hypothesis only (2609.10871) |
| AGENTS.md ([agents.md](https://agents.md/)) | AAIF-stewarded; no versioned spec | Hosts disagree on precedence. Codex concatenates root-down with a 32 KiB cap; Claude Code reads AGENTS.md only when no CLAUDE.md exists. KB evidence on instruction files (P01): none |
| ACP ([v2 draft](https://agentclientprotocol.com/announcements/acp-v2-draft)) | v1 stable, v2 draft (2026-07-20); governed by Zed and JetBrains, no foundation | Competes with VS Code's Agent Host Protocol for the editor slot |
| OpenTelemetry GenAI ([agent spans](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md)) | Agent and tool spans at "Development"; moved to a separate repo with no tagged release | Don't bind `qr eval` records to `gen_ai.*` attributes yet |
| OWASP | LLM Top 10 2026 (Aug 2026; Excessive Agency now #3); Agentic Top 10 (Dec 2025); MCP Top 10 beta | Maps onto `qr policy` (tool misuse, privilege) and the workflow-injection findings in `dag.md` |
| NIST | AI RMF 1.0 (under revision); CAISI AI Agent Standards Initiative (2026-02-17); NCCoE agent identity concept paper, whose first use case (2026-09-29) is agents in the SDLC; agent control overlays planned for 2027 | No final agent guidance yet. The NCCoE work is the one to watch for `qr policy` |
| ISO/IEC 42001 | 2023 edition; SC 42 has no agentic work item | Management-system scope only |
| Workflow graphs | No standards-body standard. CNCF Open Workflow Spec v1.0.3 (MCP/A2A call tasks); OpenAPI Arazzo 1.1; LangGraph is a library; GitHub Agentic Workflows in public preview (2026-06-11) | Supports `dag.md`: no portable graph format to adopt |
| Healthcare and education | ONC HTI-1 decision-support rules in force, HTI-5 only proposed; FDA CDS guidance reissued 2026-01-29; no AI-specific HIPAA guidance; 45 CFR 92.210 in force; ED AI letter of July 2025 (FERPA) | None regulates coding agents directly. They apply where agent-built code touches ePHI, certified health IT or student records. Keep PHI and privacy checks executable |

**The research lags the standards.** The KB has no evidence paper that
evaluates MCP as an integration layer (P04: 0 supporting, 2 mixed), none
on instruction files (P01), and only a hypothesis on A2A security. The
standards change faster than the papers can measure them.

**What follows for `qr`:**
- **Claude Code stamp:** `qr init --host claude-code` stamps a
  CLAUDE.md that imports `@AGENTS.md`. That stays correct, because
  Claude Code skips AGENTS.md whenever a CLAUDE.md exists.
- **Codex size cap:** `qr lint instructions` counts lines, not bytes.
  A 32 KiB check for Codex would be a small, deterministic addition.
- **MCP auth changes:** `qr` keeps tokens in the environment and does
  not speak MCP, so the auth changes need no code here. Gortex and the
  Sonar MCP server must track the `2026-07-28` revision themselves.
