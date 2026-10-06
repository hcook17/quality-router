# Contribution rubric (second gate: quality over quantity)

`REVIEW_RUBRIC.md` asks whether a paper's evidence can be trusted. This
rubric asks a different question: **what does the paper add that a team
can act on?** A paper can be rigorous and still add nothing new, for
example a leaderboard, a restated survey, a system tour, or a renamed
known practice. Such a paper counts toward volume, not evidence, and it
must not back a gate or a steer.

One file per paper: `contributions/<arxiv_id>.json`. The reviewer reads
the full text (`raw/text/<id>.txt`) and the existing review
(`reviews/<id>.json`, plus `audits/<id>.json` if present). The stance is
adversarial: assume the paper adds nothing until a specific passage shows
otherwise.

## Contribution kinds

| kind | Counts when the paper gives… | Does not count |
|---|---|---|
| `heuristic` | an actionable rule with a condition or threshold ("when X, do Y"; "below N, Z fails") | "careful design matters" |
| `nuance` | a boundary condition that qualifies a known pattern: when it fails, for whom, at what cost, with a measured effect | "results vary by task" with no measurement |
| `design_pattern` | a reusable structure with its forces and consequences, shown to work | a system diagram of the authors' own tool |
| `anti_pattern` | a recurring practice shown to hurt, with the failure mechanism | a list of "challenges" |
| `constraint` | a hard limit, invariant or capability ceiling, with evidence | speculation about limits |
| `test_practice` | test, oracle, TDD or verification practice with evidence (what to assert, when to write tests, what a gate should check) | "tests are important" |

Each contribution has these fields:

- `statement`: one sentence a Java backend lead could act on. If it
  cannot be written specifically, it is not a contribution.
- `evidence`: the section, table or figure, and what it shows.
- `strength`: `strong | moderate | weak | unsupported`. This may not
  exceed the strongest claim in the review after the audit merge; the
  loader caps it.
- `novelty`:
  - `new`: not in any other KB paper and not a known pre-2026 practice.
  - `refines`: adds a condition, magnitude or failure mode to something
    known. Name what it refines in `relative_to`.
  - `duplicates`: another KB paper shows the same thing with equal or
    better evidence. Name it in `relative_to`.
  - `restates_known`: established practice (for example "run the tests
    in CI", "least privilege", "retrieval helps long context"). Name it
    in `relative_to`.
- `transfers`: `direct` (applies to a multi-repo Java backend team using
  coding agents), `indirect`, or `no`.

## Quantity flags (any that apply)

`leaderboard_only`, `system_description_only`, `survey_restatement`,
`renamed_known_idea`, `numbers_without_mechanism` (effect reported, no
account of why, so nothing transfers), `position_without_evidence`,
`salami_slice` (near-duplicate of the same authors' other KB paper),
`self_declared_incomplete` (work in progress, evaluation pending).

## Gate (deterministic, in `etl.py`)

A contribution **qualifies** when its strength is `strong` or `moderate`,
its novelty is `new` or `refines`, and it transfers `direct` or
`indirect`.

| Outcome | Rule | Effect |
|---|---|---|
| `contributes` | at least one contribution qualifies, and no `self_declared_incomplete` flag | keeps its review status and weight |
| `hypothesis` | no qualifying contribution, but one with `new`/`refines` novelty that transfers (evidence weak or unsupported), **or** it is flagged `self_declared_incomplete` | weight 0; listed as an open hypothesis; cannot back a gate |
| `no_contribution` | everything else, including only `duplicates` / `restates_known` | weight 0; excluded from evidence |

The reviewer's `proposed` value (`keep | hypothesis_only | drop`) can
only tighten the outcome. A rejected review stays rejected. A withdrawn
paper (arXiv comment says withdrawn) and a paper whose v1 date is
outside the window are rejected before either gate runs.

## JSON shape

```json
{
  "arxiv_id": "2606.18168",
  "contributions": [
    {"kind": "test_practice",
     "statement": "Gate new agent-written test files on at least one value-level assertion; presence of a test file is not verification.",
     "evidence": "§III-A Fig. 1: strong-oracle rate 18-67% on new files by agent; 86.7% classifier agreement with humans.",
     "strength": "moderate", "novelty": "new", "relative_to": [], "transfers": "direct"}
  ],
  "quantity_flags": [],
  "proposed": "keep",
  "reason": "One or two sentences: what survives the cut, or why nothing does."
}
```
