# What completes the developer workflow?

Short answer: **add a harness-owned frame and a read-only, cited
exploration pass in front of the spec, and keep the spec-driven path
you already have.** The agent does not discover the domain and then
write the spec. A person promotes runnable examples and domain facts
into the spec. Explanations are not the safeguard for a new developer.

Evidence base: 149 papers added for this question (topics T62–T69,
first submitted 2026-05-01 through 2026-10-07), every review-passing
paper blind-audited. Patterns P38–P43 were added to `taxonomy.json`.
Regenerate: `python3 etl.py load && python3 etl.py report && python3
etl.py robustness`. Of the 149, **40 are evidence**, 29 are hypothesis
only, 3 add nothing transferable, and 77 were rejected (one because
the authors discarded the experiments: 2608.28421).

| Pattern | Supports / contradicts / mixed | Label (`kb_robustness.md`) |
| --- | --- | --- |
| P38 Pre-spec knowledge discovery | 1 / 0 / 1 | leaning |
| P39 Machine-readable domain context | 4 / 0 / 6 | conditional |
| P40 Clarifying questions before implementing | 0 / 0 / 4 | unresolved |
| P41 Comprehension and skill safeguards | 0 / 1 / 3 | contested |
| P42 Requirement-to-code traceability | 0 / 0 / 0 | none |
| P43 Codebase question answering / exploration | 5 / 0 / 4 | consensus |

P43 and P38 do not survive the subsets that matter for this team.
P43 falls to unresolved on the 25 Java-evaluated evidence papers and
when SWE-bench papers are removed. P38 falls to none on both of those
subsets, and to unresolved without its one supporting paper. P39
stays conditional on the September 30 cutoff and becomes unresolved
only on the Java subset. P40, P41 and P42 do not change label on that
cutoff.

## The stages

### 1. The harness fills the frame. The agent does not decide to ask.

P40 is unresolved: no evidence paper shows that letting the agent ask
clarifying questions wins. The papers that measured asking name the
conditions.

- **Empty required slots block the run.** Ambig-DS (2605.09698, E)
  gave five models a one-question channel with a truthful oracle. The
  channel won, and the agents still asked on tasks that were fully
  specified and skipped tasks that were not. The harness should own
  the slots (target repository, branch, environment, entity, success
  metric, output form) and force one question to a person when a slot
  is empty.
- **Naming the target is the question that matters.** In 2607.02294
  (E), acted-run safe success was 67.9% with a unique target and fell
  once several candidates matched. Writing "production" or "shared" in
  the prompt left the action rate at 65.5% versus 64.0%.
- **More questions are not the lever.** ICAE-Bench (2607.21217, E)
  raised pass rate from 37.4% to 61.8% by committing the same
  acceptance examples as runnable fixtures. Budgets of 24 questions
  did no better than 16. CONTRA (2610.01769, E) improved question
  quality by 14 points and pass rate by 0.6–1.2 points. Drop any
  question the ticket already answers, and require a quoted span.

### 2. Domain context is a versioned card the agent looks up.

P39 is conditional. Four evidence papers support it and six are mixed.
The mixed papers are the design rule: fetch the slice the task needs,
and do not paste the whole manual.

- A YAML contract fetched rule by rule lifted hard-task accuracy by
  about 19–36 points over the same tools with an empty contract, and
  beat the same knowledge pasted as a 24k-character manual
  (2609.22259, E).
- A fault taxonomy plus symptom-to-cause rules gained 8.6–21.6
  Full-match points over topology alone (2607.13548, E). One model,
  one run.
- Removing issue-specific semantic cards dropped file Hit@10 by 6
  points with the output size unchanged (2609.31176, E). Single runs,
  small models.
- Retrieving security-guideline records beat inferred weakness labels
  alone (2608.25457, E).
- Metadata cards did not clear their own run band (2606.22906, E):
  the ablation moved full recall from 85.8% to 82.2%, inside a run
  range of 80.0–90.0. A file-recovery plugin at about 10% micro
  precision is not a context package: on 27 medium tasks, about nine
  of ten returned files were outside the expert set.
- When the same skill file is copied across repos, pin the upstream
  version and fail the build when it moves. Of 2,462 linked copies,
  74.8% landed near-verbatim, and 40.2% of the never-edited copies
  had already missed an upstream change (2607.00911, E).

### 3. Before an edit, run a read-only pass that returns cited answers.

This is the one supported form of P38, and it is agent-side discovery
before a fix, not a human writing a spec. Know Before Fix
(2607.11111, E) prepended two cited repository answers and raised
Pass@1 by 3.8 points (58.4 to 62.2, GPT-5-mini) and 4.4 points (66.4
to 70.8, DeepSeek-V3.2). One root-cause proposal instead of those
answers dropped DeepSeek to 66.0, below the agent with no preamble.
Single runs, Python only, and the question count was chosen on this
benchmark family.

P43 is consensus on the full set (5 supporting, 0 contradicting, 4
mixed) and unresolved once SWE-bench papers are removed:

- Exploration agents beat one-shot embedding retrieval on four
  backbones. On a 30-question Java subset the agents scored 59–63
  against 47–49, at about 13 times the tokens (2608.24221, E).
- Under a fixed budget of five regions, multi-step exploration beat
  one-shot BM25 and TF-IDF. With the agent held fixed, six models
  still sat at line recall 0.052–0.185 while file hit was 0.343–0.655
  (2606.07297, E). Score the explorer on line recall. The gold lines
  are reads from agents that had already solved the issue.
- Path prefixes on AST chunks raised dense Top-10 from 0.703 to
  0.873. File Top-1 near 80% is not a fix rate: swapping the localizer
  in raised best-of-three resolves from 86/300 to 108/300
  (2605.17965, E).
- A few on-demand graph probes raised SWE-bench Pro by 20, 35 and 46
  of 731 and lost 6 on one Go repository. A text dump of the same
  edges added almost nothing, and there is no Java front end
  (2607.01929, E). The stance is mixed.
- If the repair stage can still open the repository, a smaller
  explorer kept 78–94% of a stronger model's file Hit@3 at 84–95%
  fewer tokens (2608.29675, E). The file list is a hint. Exact match
  was 0.30–0.57, so it is not a fence around the repairer.

Do not publish the answers. On SWE Atlas (2605.08366, E) the best
agents met every expert must-have on about 41% of onboarding,
architecture and root-cause questions. Run the pass read-only, with
outbound network denied: "run the tests" on freshly pulled code had
45.5% exfiltration success (2608.30686, E), and a networked doc eval
fetched the upstream answer in 26 of 85 runs (2609.39909, E).

### 4. The spec is the promoted artifact. Then the existing path.

Commit the acceptance examples as runnable fixtures before
implementation (2607.21217, the 37.4% to 61.8% result above). When a
later request adds a feature, simplicity or latency constraint,
restate the security property in the acceptance criteria: that
pressure flipped 56.4–61.2% of previously secure Python functions, and
a one-line "be secure" reminder did not stop it (2605.10133, E). The
98% figure in that paper is the arm that explicitly says to prefer
flexibility over the control.

Then the separate test author, the lock, implementation, and the
gates. A static dependency graph missed 137 of 984 downstream breaks,
about 16% (2610.04940, E), so cross-repo impact stays "run the
consumer suites."

P42 has no evidence paper. TraceDev (2607.18886) is a hypothesis: its
success rate counts tests an unvalidated model judge passed first.
Agent-written requirement links stay unreliable. The earlier Java
result is about 0.2 F1 (2606.24834, E).

### 5. Comprehension safeguards are checks, not explanations.

P41 is contested, and the only contradicting evidence paper is the
one that isolated explanations. Adding a natural-language explanation
did not improve accuracy at judging assertion correctness, and
reviewers caught about half of the incorrect assertions while staying
confident (2607.08885, E). Accept an agent-written function comment
only when regenerating the body from that comment passes the existing
tests. A same-model judge was right for 66.4% of the comments it
accepted (2606.22247, E). Check explanations of legacy code against
tests or data flow before storing them: misleading identifiers, not
terse ones, steer the explanation (2609.26388, E).

After adoption, do not read a stable author count as intact
onboarding. Across 2,808 repositories the newcomer share of human
pull-request authors fell 3.7 points (2606.26289, E). Per-function
complexity rose about 3% cyclomatic, and about 11% cognitive in
Python, once pre-existing trends were removed (2607.01810, E).

A rule file is what repositories actually adopt, and it is not a
finished harness. Of 2,732 popular repositories, 2.6% had four or
five of the five path-detected artifacts. In 150 coded rule-file
repositories, decision rationale was 10–27% and acceptance criteria
were 10–20% (2609.32014, E). Add the decision record and the
checkable criterion as separate files.

## What would change this answer

- A same-model comparison, on this team's Java repositories, where a
  read-only question pass before the edit beats the same agent without
  it on resolve rate, not only on a SWE-bench subset.
- An isolating comparison where an agent-written spec, produced after
  repository exploration, beats a human-written spec with the same
  acceptance fixtures. None was found. PRAXIS (2608.19784) is a
  hypothesis: the gain is a few tasks on one run, and the practice
  task was built from the hidden function body.
- A developer study where an explanation raised accuracy at a
  judgment the team actually makes. 2607.08885 found the opposite.

## Where `qr` could help (not built)

- **`qr discover new`:** create a discovery record with the required
  slots. Refuse to start implementation while a slot is empty.
- **`qr discover lint`:** check that a domain card names its upstream
  version, that exploration notes carry file:line citations, and that
  acceptance examples are runnable files rather than prose.
- **`qr lint knowledge`:** on a documentation or card diff, require an
  explicit "no update needed" outcome to be available, and fail a
  copied skill whose pinned upstream has moved (2607.00911, 2609.39909).

Any of these would be built the same way as the spec-driven harness:
spec, a separate test author, lock, implement, then a held-out check.
