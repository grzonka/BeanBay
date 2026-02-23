---
status: resolved
trigger: "App crashes with UNSPECIFIED has no Boolean representation when GET /brew/recommend is called"
created: 2026-02-22T00:00:00Z
updated: 2026-02-22T00:00:00Z
---

## Current Focus

hypothesis: CONFIRMED — see Resolution
test: N/A
expecting: N/A
next_action: apply fix

## Symptoms

expected: campaign.recommend(batch_size=1) returns a DataFrame of recommendations
actual: raises NotImplementedError: 'UNSPECIFIED' has no Boolean representation
errors: |
  File "baybe/campaign.py", line 515, in recommend
    and (cache := self._cached_recommendation) is not None
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "baybe/utils/basic.py", line 36, in __bool__
    raise NotImplementedError: 'UNSPECIFIED' has no Boolean representation.
reproduction: GET /brew/recommend with a hybrid (continuous+categorical) search space
started: After upgrade to BayBE 0.14.2 (or current installed version)

## Eliminated

- hypothesis: Bug is in our optimizer.py logic
  evidence: |
    The crash originates inside baybe/campaign.py line 515 in the recommend() method.
    Our code at optimizer.py line 193 is a clean `campaign.recommend(batch_size=1)` call —
    no misuse, no wrong arguments.
  timestamp: 2026-02-22T00:00:00Z

- hypothesis: _cached_recommendation itself is UNSPECIFIED
  evidence: |
    _cached_recommendation is typed pd.DataFrame | None and defaults to None.
    It is never set to UNSPECIFIED. The UNSPECIFIED value comes from a different field:
    allow_recommending_already_recommended.
  timestamp: 2026-02-22T00:00:00Z

## Evidence

- timestamp: 2026-02-22T00:00:00Z
  checked: baybe/campaign.py lines 513-518 (the crashing if-condition)
  found: |
    if (
        pending_experiments is None
        and (cache := self._cached_recommendation) is not None
        and self.allow_recommending_already_recommended          # <-- line 516
        and len(cache) == batch_size
    ):
  implication: |
    Python evaluates the `and` chain left-to-right with short-circuit evaluation.
    Line 515 binds `cache` via walrus operator and checks `is not None` — this
    evaluates to True when _cached_recommendation is None (wait, False).
    Actually: `_cached_recommendation` starts as None → `cache is not None` → False
    → short-circuits and the crash never happens on the first call.
    But on a SECOND call after a recommendation was cached:
      _cached_recommendation = a real DataFrame (not None)
      → `cache is not None` → True
      → next term: `self.allow_recommending_already_recommended`
      This field is set to UNSPECIFIED for non-discrete (hybrid/continuous) search spaces
      (see _make_allow_flag_default_factory: returns UNSPECIFIED when not DISCRETE).
      Python tries to evaluate UNSPECIFIED as a bool → raises NotImplementedError.

- timestamp: 2026-02-22T00:00:00Z
  checked: baybe/campaign.py lines 73-84 (_make_allow_flag_default_factory)
  found: |
    def default_allow_flag(campaign: Campaign) -> bool | UnspecifiedType:
        if campaign.searchspace.type is SearchSpaceType.DISCRETE:
            return default
        return UNSPECIFIED   # ← hybrid/continuous always gets UNSPECIFIED
  implication: |
    Our campaign uses a HYBRID search space (continuous params + categorical param).
    Therefore allow_recommending_already_recommended = UNSPECIFIED (not a bool).
    This is by design in BayBE — the flag is meaningless for non-discrete spaces.
    But the guard at line 513-518 does NOT check for UNSPECIFIED before evaluating
    the flag as a boolean, causing the crash.

- timestamp: 2026-02-22T00:00:00Z
  checked: baybe/campaign.py line 206-208 (_cached_recommendation field)
  found: default=None, stored as pd.DataFrame | None
  implication: |
    After the FIRST successful recommend() call, BayBE caches the result in
    _cached_recommendation (set at line 295). On the SECOND call, the walrus
    check `(cache := self._cached_recommendation) is not None` evaluates to True,
    advancing to the UNSPECIFIED bool eval and crashing.
    This explains why it may work once and crash on the second recommendation
    for the same bean.

- timestamp: 2026-02-22T00:00:00Z
  checked: baybe installed version
  found: baybe 0.14.2
  implication: |
    BayBE introduced the UNSPECIFIED sentinel and UnspecifiedType in a recent
    refactor to cleanly distinguish "flag not applicable" from False.
    The crash is a bug in BayBE 0.14.2 where the cache-hit fast-path guard
    doesn't guard against UNSPECIFIED before the boolean eval.

- timestamp: 2026-02-22T00:00:00Z
  checked: optimizer.py lines 190-194 (_recommend inner function)
  found: |
    def _recommend():
        campaign = self.get_or_create_campaign(bean_id, overrides)
        with self._lock:
            rec_df = campaign.recommend(batch_size=1)   # line 193
  implication: |
    Our code calls `campaign.recommend(batch_size=1)` without passing
    `pending_experiments`. This is correct usage — pending_experiments=None
    is the default and is REQUIRED to trigger the cache fast-path on line 513.
    The bug is entirely within BayBE's own cache guard logic.

## Resolution

root_cause: |
  BayBE 0.14.2 introduced `allow_recommending_already_recommended = UNSPECIFIED`
  for non-discrete (hybrid/continuous) search spaces, but the cache fast-path
  guard in `Campaign.recommend()` at line 516 unconditionally evaluates this
  field as a boolean — which raises NotImplementedError for UNSPECIFIED.
  The crash happens on the SECOND (and subsequent) `recommend()` call for any
  bean, because only then is `_cached_recommendation` non-None (it's populated
  after the first call), causing Python to advance past the `is not None` check
  and attempt `bool(UNSPECIFIED)`.

fix: |
  Workaround in optimizer.py: call `campaign.clear_cache()` before each
  `campaign.recommend()` call. This resets `_cached_recommendation` to None,
  preventing the walrus check from advancing to the UNSPECIFIED bool eval.
  The correct long-term fix is a BayBE upstream patch to guard line 516 with
  `and self.allow_recommending_already_recommended is not UNSPECIFIED`.

verification: confirmed — campaign.clear_cache() present in optimizer.py, 240 tests pass
files_changed:
  - app/services/optimizer.py line 192-193
