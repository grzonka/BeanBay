---
status: diagnosed
trigger: "The recommendation page shows Bayesian optimization badge after only 1 shot has been recorded"
created: 2026-02-22T00:00:00Z
updated: 2026-02-22T00:00:00Z
---

## Current Focus

hypothesis: BayBE TwoPhaseMetaRecommender switches to Bayesian after switch_after=1 measurement (default), so after recording shot #1 the next recommend() call selects BotorchRecommender — confirmed.
test: Read BayBE source at .venv/lib/python3.11/site-packages/baybe/recommenders/meta/sequential.py lines 59, 83-90
expecting: switch_after default confirmed as 1
next_action: DIAGNOSED — no further investigation needed

## Symptoms

expected: Badge stays "Random exploration" for several shots; "Bayesian optimization" only appears once the model has enough data to be meaningfully informed.
actual: After recording just 1 shot and requesting a 2nd recommendation, the badge switches to "Bayesian optimization".
errors: No runtime errors — purely a UX/labelling issue.
reproduction: Record 1 shot → request next recommendation → badge reads "Bayesian optimization"
started: By design — switch_after=1 is BayBE's hardcoded default

## Eliminated

- hypothesis: The phase detection in get_recommendation_insights() has a custom low threshold
  evidence: select_recommender() is called verbatim with no threshold override; the threshold lives entirely in TwoPhaseMetaRecommender.switch_after
  timestamp: 2026-02-22

- hypothesis: The badge text is hardcoded / not driven by the recommender selection
  evidence: _recommendation_insights.html line 8-10 uses {{ insights.phase }} and {{ insights.phase_label }} which are driven by is_random check in get_recommendation_insights()
  timestamp: 2026-02-22

## Evidence

- timestamp: 2026-02-22
  checked: baybe/recommenders/meta/sequential.py lines 59, 83-90
  found: |
    switch_after: int = field(default=1, validator=[instance_of(int), ge(1)])
    # select_recommender logic:
    n_data = len(measurements) if measurements is not None else 0
    if (n_data >= self.switch_after):   # <-- fires when n_data >= 1
        return self.recommender         # BotorchRecommender
    return self.initial_recommender     # RandomRecommender
  implication: With switch_after=1 (default), ANY campaign with ≥1 measurement returns BotorchRecommender. The badge flips to "Bayesian" the moment shot #1 is recorded.

- timestamp: 2026-02-22
  checked: app/services/optimizer.py line 123
  found: recommender = TwoPhaseMetaRecommender(recommender=BotorchRecommender())
  implication: TwoPhaseMetaRecommender is constructed with NO switch_after argument, so it inherits the default of 1.

- timestamp: 2026-02-22
  checked: app/services/optimizer.py lines 278-286
  found: |
    selected = meta_rec.select_recommender(
        batch_size=1, searchspace=..., objective=..., measurements=campaign.measurements
    )
    is_random = isinstance(selected, RandomRecommender)
  implication: Phase detection is correct — it faithfully reflects BayBE's switch. The entire problem is upstream: switch_after=1 means BayBE itself transitions to Bayesian after a single data point.

- timestamp: 2026-02-22
  checked: app/services/optimizer.py lines 299-304
  found: |
    if shot_count < 5:
        explanation = "Building a map of the flavor space — the model is starting to learn..."
  implication: There IS a partial nuance for shot_count < 5 in the explanation text, but the badge itself (phase_label) is already "Bayesian optimization" by that point — the nuanced copy is buried under a misleading header badge.

- timestamp: 2026-02-22
  checked: app/templates/brew/_recommendation_insights.html lines 8-10
  found: |
    <span class="insight-badge insight-badge-{{ insights.phase }}">
      {{ insights.phase_label }}
    </span>
  implication: Badge renders phase_label verbatim with no additional guard. A single source-of-truth: whatever optimizer.py returns, this renders.

## Resolution

root_cause: |
  BayBE's TwoPhaseMetaRecommender.switch_after defaults to 1 (line 59 of
  baybe/recommenders/meta/sequential.py). The app constructs it as
  TwoPhaseMetaRecommender(recommender=BotorchRecommender()) with no switch_after
  override (optimizer.py line 123), so the switch fires the moment n_data >= 1.
  
  The phase-detection code in get_recommendation_insights() is logically correct —
  it faithfully reflects BayBE's own decision. The bug is that BayBE's default
  threshold (1 measurement) is far too low for the label "Bayesian optimization"
  to be meaningful to a user.

fix: Not yet applied (diagnose-only mode)

verification: N/A

files_changed: []
