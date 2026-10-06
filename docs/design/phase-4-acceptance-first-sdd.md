# Phase 4: acceptance-first SDD (the Spec stage, executable)

**Status:** implemented under `src/quality_router/harness/` (`specdoc.py`,
`scaffold.py`, `acceptance.py`, `junit_feedback.py`) + `tests/harness/`.
Evidence: `research/harness-kb/FINDINGS.md`. Demo:
`examples/content-pipeline/run-demo.sh`. Builds on phase 3
(`docs/design/phase-3-harness.md`).

## The steer

The org is rolling out spec-driven development top-down as
Research (UX) → Frame (Product) → Spec (Design + Eng) → Gate (QA + Accessibility).
The KB does not support SDD *as a methodology* (P14: 2 supporting, 12
introduce-only, three framework papers rejected for having no
evaluation). It does support the narrow thing inside it: **structured
acceptance criteria with a precise output contract** (P34: 7 supporting,
0 contradicting). So keep the four stages and change what the Spec stage
produces and what the Gate stage trusts:

| Stage | Drop | Do instead | Basis |
| --- | --- | --- | --- |
| Research | Agent-written "user needs" as evidence | Human research; record the outcome metric the change should move | [J] |
| Frame | Long PRDs pasted into the agent's context | One-line problem, out-of-scope list, owner, repos touched | [E] 2605.06445 constraint decay |
| Spec | Prose specs, SDD templates with many MUST/SHALL lines | `qr spec new`: criteria (`### AC-n`) each with an **example table**, a `Contract:` line, under 120 lines. `qr spec lint` must pass | [E] 2609.08149 (21 of 102 failures from unstated constants/defaults), 2609.22222 (under-specified contract: 23.4 pp swing), 2605.06445 |
| Spec | Layer/ORM/transaction rules as prose | ArchUnit or a static check, tagged `[check: Name]` | [E] 2605.06445 |
| Spec → Gate | Tests written by the agent that writes the code | `qr spec scaffold` generates JUnit tests from the example rows; a human binds and reviews them; `qr spec lock` pins them | [E] P15 self-consistent wrong tests; 2605.17242 |
| Gate | LLM reviewer or "tests pass" as the merge gate | `qr gate acceptance` + phase-3 gates; LLM review advisory only | [E] 2606.01629, 2607.18057, 2606.18168 |
| Gate | AGENTS.md rules as enforcement | Policy hook makes locked files read-only to the agent | [E] 2608.23550 |
| All | "SDD works" claims | A measured pilot (below) with `qr eval` | [E] 2607.03691, 2606.12344 |

[E] = backed by admitted KB evidence (all caveated; the best paper scores
rigor 4/5). [J] = engineering judgment where the research is silent.

## The proposal being implemented

2605.17242 (TDDev) is the closest measured design: derive acceptance
tests from requirements, then loop the agent against them; +15.5 to
+23.7 pp with capable models. The blind audit adds two caveats that
shape this design:

1. Part of the gain is **test visibility**: the loop saw the same tests
   the oracle scored. So the implementing agent should *read* the
   acceptance tests. The lock blocks writes only.
2. The gain disappears with an unreliable verifier. So the tests come
   from the spec's examples (not from the implementing agent), a human
   approves them, and the gate checks they were not changed.

Agents editing their own verification is documented for self-improving
agents (2609.00069: tampering in 18–85% of iterations, rated a weak
claim; 2607.24300: self-scores stay high while hidden results regress). Applying that to
coding agents editing locked tests is by analogy [J]; the demo shows the
mechanism.

## Flow and owners

```
Frame (Product)      one-line problem, owner, repos
Spec  (Design+Eng)   qr spec new -> write examples -> qr spec lint        (coordination repo)
      (Eng)          qr spec scaffold --bind ...  -> review the generated JUnit
      (QA lead)      qr spec lock --approved-by ... -> commit "spec: approve AC-n"  (service repo)
Build (agent)        implement; reads locked tests; hook blocks edits to them
                     on red: qr feedback junit -> AC id, spec example row, app frames
Gate  (CI)           qr gate acceptance --base origin/main + phase-3 gates
```

The lock commit is the human approval. Put `.quality-router/acceptance.lock.json`
under CODEOWNERS for the spec owner so GitHub enforces the review.

## Commands

Exit 0 pass, 1 fail, 2 usage error (with an example on stderr).
`--json` where offered.

| Command | Does | Fails when |
| --- | --- | --- |
| `qr spec new --title T --out F [--contract P] [--dry-run]` | Writes a short spec template that lints clean once the contract exists | F exists (exit 2) |
| `qr spec lint --spec F... [--root DIR]... [--strict]` | Parses criteria, example tables, `Contract:` | Errors: no criteria, duplicate id, criterion without an example table (inline-only example → info), ragged row, table without input+output, contract not found (spec dir, its ancestors, `--root`), TBD/TODO/FIXME. Warnings: no contract, vague terms (`appropriate`, `gracefully`, `as needed`, `etc`, …), structural MUST/SHALL without `[check:]`, >120 lines |
| `qr spec scaffold --spec F --out JAVA [--package P] [--class C] [--ac ID]... [--bind AC[.col]=EXPR]... [--force] [--dry-run]` | Refuses an unlinted spec. One `@ParameterizedTest` per table: `@Tag("AC-n")`, `@CsvSource(textBlock)` rows copied from the spec, `assertEquals(expected, Objects.toString(EXPR, null))` | Unknown `--ac`, no tables, column names that collide as Java identifiers, existing file without `--force` |
| `qr spec lock --spec F... --tests GLOB... [--ac ID]... [--approved-by WHO] [--dry-run]` | Writes `.quality-router/acceptance.lock.json`: sha256 + criteria per spec and test, owned criteria | Spec does not lint clean; an owned criterion has no locked test |
| `qr gate acceptance [--root .] [--base REF]` | Reads the lock and git history | A locked test changed or was removed; a locked spec changed; the lock commit also changes `src/main`; with `--base`, an implementation commit precedes the last lock commit. No lock → warning |
| `qr feedback junit --reports GLOB... [--sources DIR]... [--spec F]... [--max-frames 5]` | Reads Surefire/Gradle/console-launcher XML | Any failure/error (exit 1); no reports (exit 2) |
| `qr policy check --write --path P` | Decides a write | P is locked |

`--bind` lookup order: `AC-n.column`, then `AC-n`, then `*`. Input
columns are `String` variables named after the header (`expected title`
→ `expectedTitle` for the output). An unbound criterion compiles to
`Object actualX = null;` and fails until bound (red first).

Cell rules: `(null)` is null; a backticked cell is verbatim (keeps
whitespace, `` `` `` is the empty string); `\|` escapes a pipe. Columns
whose header starts with `expected ` are outputs; with none, the last
column is.

## Lock-aware policy

When `.quality-router/acceptance.lock.json` exists (searched upward from
the hook's cwd), the hook denies, independent of `policy.json`:

- file-tool writes (Claude `Write/Edit/MultiEdit/NotebookEdit`, Cursor
  `preToolUse` Write/Delete) to a locked test, spec or the lock;
- shell commands that name a locked path alongside a write verb (`rm`,
  `mv`, `cp`, `tee`, `>`, `sed -i`, `perl -i`, `git checkout/restore/rm`, …);
- `qr spec lock` (also in the default `policy.json` deny list).

Reads stay allowed (caveat 1 above). An unreadable lock fails closed.
Shell detection is best effort; `qr gate acceptance` is the backstop.

## Pilot (how to steer the org with data, not claims)

Run on one service repo for one sprint, then decide.

- **Arms:** (A) the org's current prose-spec flow; (B) acceptance-first.
  Same host + version + model, pinned.
- **Tasks:** 20–50 recent tickets from your own repos, prepared with
  `qr eval prepare --hidden <reference tests>` (no history, egress
  blocked).
- **Primary metric:** resolve rate on hidden reference tests,
  `qr eval report` (Wilson CIs). **Secondary:** reviewer fix-up commits
  per merged PR (2605.22534), tokens per resolved task, spec-lint
  findings at Spec review, hook denials in the audit log.
- **Decide:** adopt B if its resolve rate is higher with non-overlapping
  CIs, or equal with fewer reviewer fix-ups. If the CIs overlap at n=50,
  say so; do not claim a win.
- `qr feedback junit` is a separate hypothesis (2609.00362 and
  2609.22222 found little gain from richer diagnostics). Ablate it within
  arm B before keeping it in the loop.

## Invariants

- Same as phase 3: no model call in `harness/`; reads reports, never runs
  Maven/Gradle; reads cross-repo (specs in the coordination checkout),
  writes only the repo it is pointed at; stdlib only.
- `qr spec lock` is a human action. The hook refuses it from an agent.
- No lock → the acceptance gate warns and the hook ignores locks
  (disconnected no-op).

## Known limits

- Scaffolded tests compare strings (`Objects.toString`). Typed or
  structured outputs need a bind expression that renders them, or a
  hand-written test tagged with the AC id (then lock that file instead).
- The lock pins bytes, not meaning: reformatting a locked test fails the
  gate. Re-scaffold, review, re-lock in a spec-only commit.
- History checks need full history in CI (`fetch-depth: 0`). Without the
  lock commit in history the gate warns `lock_history_unavailable`.
- A locked spec outside the checkout (coordination repo) is only
  hash-checked when CI checks it out at the same relative path; otherwise
  it warns `spec_not_checked_out`.
- Healthcare/education specifics (PHI in logs, licensing semantics) have
  almost no research behind them (T56/T57). Keep them as executable
  checks, not spec prose.

## Verify

- `uv run pytest --cov` (floor 98.7%), `uv run ruff check src tests`.
- `examples/content-pipeline/run-demo.sh`: the prose draft fails
  `spec lint`; the executable spec passes and scaffolds 12 example rows;
  the agent's first attempt fails AC-3 `(null)` and `qr feedback junit`
  points at the spec row and `LicenseParser.java:9`; the agent's edit to
  the locked test is blocked by the hook, and the same edit from an
  unhooked host turns the build green but fails `qr gate acceptance`; the
  review fix passes all seven gates.
