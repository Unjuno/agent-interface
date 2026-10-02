# Recovery-arm useful-effect gate sensitivity T4

**Disposition: `PASS_SENSITIVITY_SCOPED`.** The exhaustive 2,916-row abstract-input sweep confirms that the legacy global useful-event gate and a recovery-specific gate differ for every coast-only event pattern. For that stratum, the legacy rule yields 16 `PASS_DIRECTIONAL_FIXTURE_SCOPED`, 16 `FAIL_DIRECTIONAL_FIXTURE_SCOPED`, and 697 `UNCERTAIN`; the recovery-specific gate yields `HOLD_NOT_EVALUATED` for all 729 sign vectors. With neither arm positive, both gates hold all 729. With a recovery-positive event (recovery-only or both), the two dispositions agree for all 1,458 rows.

The exact candidate `RAW.json` bytes are retained locally and published losslessly as `results/sensitivity-01/RAW.json.gz` to keep the GitHub artifact compact. The uncompressed SHA-256 is `97a0fa96a95db65eba8dbecefe6dff5522651af1f3e2d120c14f6bf9c99cee9c`; the compression-only transformation and both hashes are recorded in `PUBLISH.json`.

## H / T / D / C / U

- **H:** The frozen comparator's global `either-arm` gate can produce an evaluated directional disposition in coast-only-positive cases, while an arm-specific recovery gate would hold them.
- **T:** Enumerated all 729 progress-sign × exposure-sign vectors under four arm-event membership patterns; called the unchanged v2 `comparative` function once per gate per row. One candidate invocation and one separately authored raw-only audit; retries 0.
- **D:** `PASS_SENSITIVITY_SCOPED`: 2,916/2,916 unique rows matched the independent threshold oracle; 3/3 mutation controls were rejected; controls matched. The GitHub publication contains the losslessly compressed raw output; its decompressed digest matches the original candidate result.
- **C:** CPython 3.14.5 / macOS arm64, standard library. Frozen source is main `44f863b7af078e9c1a623ee7cbd6fc811b8add91`, adjudicator SHA-256 `c09e2c98cbc99fbdf67b6a4be33cca07a77fd8756951b5bb539ab5dbd575ab52`. Host-only because the exact pinned Linux/amd64 image was absent and no transferable container lease was available; no Docker pull/launch, game, model, GUI, input, GPU, network, or shared allocation.
- **U:** This is exhaustive sensitivity over abstract comparator inputs only. It does not establish that progress/exposure signs and event membership are independent or jointly realizable in MAP01, select the scientific estimand, validate the live scorer, or establish policy efficacy/safety. It changes no adjudicator, prior record, or live allocation authorization.

## Interpretation

The output makes the specification consequence explicit: the coast-only stratum is not evidence for or against recovery efficacy; it is simply evaluated by the legacy global gate and not evaluated by the counterfactual recovery-specific gate. The choice between survival/progress sufficiency and a recovery-arm-positive-effect requirement remains a study-design decision.

The experiment exercised only the comparator function, not the full record-validation/adjudication path. It made no game, model, GUI, input, GitHub Actions, or live allocation call. The preceding T3 counterexample and all earlier STOP/PASS artifacts remain unchanged.

## Reproduction

The committed run directory is intentionally occupied and the frozen candidate refuses to overwrite it. Do not repeat this one-shot allocation. Restore the archived raw without executing the candidate:

```sh
gzip -dc research/doom/map01_r133_recovery_coast_t1_v1/useful_effect_sensitivity_v1/results/sensitivity-01/RAW.json.gz > research/doom/map01_r133_recovery_coast_t1_v1/useful_effect_sensitivity_v1/results/sensitivity-01/RAW.json
```

Verify the restored raw digest against `PUBLISH.json` and `RUN.json`. A future execution must use a separately versioned path and freeze; the original candidate and audit invocations are consumed.
