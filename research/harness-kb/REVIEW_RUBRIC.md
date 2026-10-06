# Adversarial review rubric

Every candidate paper gets one review file `reviews/<arxiv_id>.json` before it
enters the knowledge base. The reviewer's stance is **adversarial**: assume the
headline claim is overstated until the paper's own evidence shows otherwise.
The reviewer proposes a verdict; `etl.py load` applies a deterministic gate
that can only tighten it (see `admission()`).

Inputs per paper: `raw/text/<id>.txt` (full text), `signals/<id>.json`
(affiliations, vendor hits, code links, limitations/ack/COI sections, counts),
and the arXiv metadata in `papers.jsonl`.

## What to check

1. **Claim vs evidence.** List the 2–5 load-bearing claims. For each, find the
   table/figure/section that supports it and grade `strong | moderate | weak |
   unsupported`. Abstract numbers absent from the body are `unsupported`.
2. **Methodology.** Sample size (tasks, repos, participants), baselines (are
   they current and tuned, or strawmen?), models tested, seeds/repeated runs,
   variance or CIs, ablations, held-out splits, contamination controls.
3. **Standards.** Peer-review status (arXiv comment / journal_ref), limitations
   or threats-to-validity section, artifact release (code, data, prompts),
   pre-registration for human studies.
4. **Biases** (use these `type` values; add `other:<name>` only if none fit):
   `benchmark_overfit`, `contamination_risk`, `strawman_baseline`,
   `self_evaluation` (authors' own system judged by authors' own metric),
   `llm_judge_unvalidated`, `cherry_picked_examples`, `small_sample`,
   `single_model`, `single_language_python`, `no_variance_reported`,
   `toy_tasks`, `survivorship`, `self_reported_numbers`, `metric_mismatch`
   (metric doesn't measure the claim), `hype_language`,
   `selection_bias_participants`, `novelty_inflation` (renames known idea),
   `missing_cost_reporting`, `closed_artifacts`.
5. **Conflict of interest.** Do authors work for (or are funded by) a vendor
   whose product, model, or benchmark the paper evaluates favorably? Does a
   benchmark paper's authors also ship the top-ranked system? Is it a product
   announcement formatted as a paper? `severity`: `none | low | medium | high`.
   Vendor affiliation alone is `low`; vendor evaluating its own product
   favorably without independent replication is `high`.
6. **Conflicts with other papers.** If the paper's finding contradicts another
   paper you know is in the corpus (or in your batch), record it in
   `conflicts_with`.
7. **Applicability** to the reference team: backend **Java** team, healthcare
   education content ingestion and delivery to front ends, ingestion spans
   **≥4 repositories**, mixed agent hosts, rolling out spec-driven development.

## Scores (integers 0–5)

| Key | 0 | 3 | 5 |
| --- | --- | --- | --- |
| `rigor` | no evaluation / pure opinion | reasonable eval with gaps (no variance, one model) | multiple models, baselines, variance, ablations, held-out |
| `reproducibility` | nothing released | code or data released, partial | code+data+prompts, scripts runnable |
| `generalizability` | toy / one repo | several repos, one language | multi-language, real industrial setting |
| `relevance` | unrelated to the team | indirectly useful | directly informs a harness decision for the team |
| `coi_risk` | independent | vendor-affiliated, not self-promoting | vendor grading own product, no independent check |

## Patterns

Tag each pattern the paper speaks to with an id from `taxonomy.json`
`patterns` and a `stance`: `supports` (evidence it works), `contradicts`
(evidence it fails/hurts), `mixed`, `introduces` (proposes, little evidence),
`neutral` (mentions). A `supports` stance requires evidence, not assertion.

## JSON shape

```json
{
  "arxiv_id": "2607.03691",
  "contribution_type": "empirical",
  "summary": "Two or three sentences in plain language.",
  "claims": [
    {"claim": "...", "evidence": "Table 3: ...", "strength": "moderate", "location": "§5.2"}
  ],
  "patterns": [{"id": "P16", "stance": "supports", "note": "..."}],
  "methodology": {"sample": "...", "baselines": "...", "models": "...", "variance": "...",
                  "ablations": "...", "contamination_controls": "...", "languages": "..."},
  "standards": {"peer_review": "...", "limitations_section": true, "artifacts": "...",
                "preregistration": "n/a"},
  "biases": [{"type": "single_language_python", "detail": "..."}],
  "coi": {"affiliations": "...", "vendor_products_evaluated": "...", "funding": "...",
          "severity": "low", "detail": "..."},
  "scores": {"rigor": 3, "reproducibility": 2, "generalizability": 2, "relevance": 4, "coi_risk": 1},
  "verdict": "admit_with_caveats",
  "verdict_reason": "...",
  "applicability": "What this means for the Java multi-repo team, or why it does not transfer.",
  "conflicts_with": [{"arxiv_id": "2606.xxxxx", "detail": "..."}]
}
```
