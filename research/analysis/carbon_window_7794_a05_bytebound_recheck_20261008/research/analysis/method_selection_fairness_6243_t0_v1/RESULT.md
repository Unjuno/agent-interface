# Result — Issue #6243 T0 method validation

**Disposition:** `METHOD_PASS_SCOPED_SYNTHETIC` for the constructed accounting rule; **`HOLD_NO_MATCHED_METHOD_DATA`** for the requested existing-data feasibility rung. Issue #6243 remains open. No empirical human–agent tempo result is claimed.

## H / T / D / C / U

- **H:** Whole-task contrasts can depend on allowed/selected method mixes and acquisition horizon, even with unchanged task correctness. A null is plausible.
- **T:** Three deterministic scenarios, 11 constructed attempt-segment rows: shortcut asymmetry, failed attempt plus method switch, and equal-method null. Two blinded-to-arm-label deterministic coders annotate only the shared row schema; an independent raw-only auditor reconstructs annotations, denominators, method strata, horizon totals, and acquisition charges. Three corruptions are tested.
- **D:** Pass method validation only if coder agreement ≥0.90, all rows/costs reconstruct, the null remains equal, horizon accounting includes acquisition, and dropped-failure/erased-switch/arm-visible-coder mutations are rejected.
- **C:** The shortcut route can be a genuine capability advantage; a common-method view is descriptive and does not replace the natural end-to-end outcome.
- **U:** Synthetic timing and script agreement are not human observations, coder reliability evidence, GUI data, causal method effects, or population estimates.

## Result

- Candidate and independent raw-only auditor: one invocation each after freeze; retries: 0; independent audit errors: 0; 11/11 raw attempt rows reconstructed; agreement 11/11 (1.00); 3/3 corruptions rejected.
- Equal-method null: both arms total 22,000 ms; no spurious route advantage.
- In the planted shortcut scenario, within-method ordinary time is 10,000 ms for both arms, while natural-method time is 4,000 ms for H (shortcut) and 10,000 ms for A (ordinary). Including a one-time 35,000 ms H acquisition cost, the cumulative ordering changes with horizon: at 4 repeats H=51,000 vs A=40,000 ms; at 10 repeats H=75,000 vs A=100,000 ms. This is a deliberately constructed sensitivity case, not an observed comparison.
- The failed 7,000 ms segment and following 5,000 ms recovery segment are both retained (12,000 ms total); the switch and error remain visible.
- Feasibility audit: the retained public six-task comparison is an agent-vs-agent serial pair and says no human comparator was measured. #5592 and #6136 describe the human geometry/practice cohorts as absent/unmeasured. Therefore no eligible existing matched method ledger was found: `HOLD_NO_MATCHED_METHOD_DATA`.

## Freeze and execution

- Base: `fe37b6913f75706fc6bd536ae3afd6ed6a72b674`.
- Image: not used. Docker/OrbStack was prohibited by the active shared-container coordination gate in #5085; the running `unjuno-native-ci-6092` container was left untouched. `obstac` was not present in this environment.
- Runtime: CPython 3.14.5, host-only deterministic construction/method run; no network, GUI, model, participant, or external effect.
- Construction: one audit mismatch was found and corrected before freeze (JSON tuple/list normalization); final construction gate 11 assertions passed.
- Formal commands (after frozen hashes in `FREEZE.json`): `python3 candidate.py`; then `python3 auditor.py`; no retries.
- Local checks: Python compile, JSON parse, and 11-assertion construction suite pass. Repository-wide CI was not run: the full repository checkout is not available in this workspace and shared Docker slot is unavailable. Do not report repository CI as passed.

See `candidate.json`, `audit.json`, `RUN_RECORD.md`, and `SHA256SUMS` for retained outputs and provenance.
