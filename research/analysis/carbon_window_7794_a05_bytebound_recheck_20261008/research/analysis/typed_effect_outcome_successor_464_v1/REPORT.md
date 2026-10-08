# Issue #2076 successor — typed partial/collateral effect outcome

## H/T/D/C/U

- **H:** Per-invariant typed outcomes prevent primary-only restoration from being collapsed into complete task success.
- **T:** Freeze direct success, wrong effect, primary-only restoration, missing collateral evidence, and generation change. Compare reducer output with an explicit oracle.
- **D:** experiment.py, five typed outcome rows, raw-retention flags, generation control, and SHA-256 digest.
- **C:** Complete success requires both primary and collateral evidence; primary-only is PARTIAL_PRIMARY_RESTORED; missing or stale evidence is UNKNOWN; raw receipts remain retained.
- **U:** Real application semantics, model completion classification, latency, GUI correctness, and runtime integration remain unknown.
- **STOP:** One finite standard-library reducer fixture; no model, GUI, network, runtime, or input action.

## Result

Command: python experiment.py

- Direct correct effect: COMPLETE_SUCCESS.
- Wrong effect: FAILURE.
- Primary-only restoration: PARTIAL_PRIMARY_RESTORED.
- Missing collateral and generation change: UNKNOWN.
- No primary-only case was classified as complete success.
- Digest: 9c383b3b5fd30fa1d336366fd7ac97776142e42b9a6d57adf9dee50980f6b0fd.

**Decision: PASS_TYPED_PARTIAL_COLLATERAL_OUTCOME_SCOPED.**

This verifies only reducer safety. It does not establish model classification accuracy, real application semantics, latency, GUI correctness, or runtime promotion.
