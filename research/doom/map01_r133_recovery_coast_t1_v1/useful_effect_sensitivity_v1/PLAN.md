# Recovery-arm useful-effect gate sensitivity T4

## H / T / D / C / U

**H.** In the frozen v2 comparator, its single `useful_present` input gates every directional disposition. For each of the 729 progress/exposure sign vectors, a coast-only useful event should allow the legacy comparator to emit `PASS`, `FAIL`, or `UNCERTAIN`, while an explicitly recovery-arm-specific useful-event gate should return `HOLD_NOT_EVALUATED`. The other three arm-event patterns should yield the same legacy and recovery-gated disposition.

**T.** Enumerate all `3^3 × 3^3 = 729` directional sign vectors under four useful-event membership patterns: neither arm positive, coast only, recovery only, and both. Apply the unchanged hash-pinned v2 `comparative` function twice per row: once with the legacy global `either-arm` gate and once with the recovery-specific gate. Run the candidate once, then a separately written raw-only auditor once. Retain all 2,916 rows, summary counts, and three mutation checks.

**D.** `PASS_SENSITIVITY_SCOPED` iff all 2,916 unique combinations and both dispositions match an independent threshold oracle; the three controls (no threat, no event, positive directional control) match; all mutations are rejected; and pinned source hashes match. Otherwise retain `FAIL_AUDIT` or the exact pre-computation `STOP` without retry.

**C.** CPython 3.14.5 on macOS arm64, standard library only; frozen comparator source from main `44f863b7af078e9c1a623ee7cbd6fc811b8add91`. The exact pinned Linux/amd64 image was not present locally, and #5085 records container ownership/inventory as unknown with no transferable lease. No Docker launch, pull, game, model, GUI, input, GPU, network call, or shared resource use. The tested function is pure deterministic Python.

**U.** This exhaustively quantifies specification sensitivity over the comparator's abstract inputs. It does not establish that endpoint signs and arm-event membership are independently realizable in MAP01, select the scientifically appropriate estimand, validate a live scorer, or establish efficacy, safety, or authorization. It is not a live T1 result and changes no prior result or adjudicator.

## Frozen interpretation

The legacy gate is `recovery_positive OR coast_positive`. The counterfactual treatment-side gate is `recovery_positive`. No threshold or pair-sign rule is changed. `HOLD_NOT_EVALUATED` under the counterfactual is reported as a sensitivity result, not a correction to the frozen adjudicator.

## Reproduction

From the repository root, run `python3 -B research/doom/map01_r133_recovery_coast_t1_v1/useful_effect_sensitivity_v1/candidate.py` exactly once, then run `python3 -B research/doom/map01_r133_recovery_coast_t1_v1/useful_effect_sensitivity_v1/audit.py` exactly once. Verify `sha256sum -c research/doom/map01_r133_recovery_coast_t1_v1/useful_effect_sensitivity_v1/SHA256SUMS`.
