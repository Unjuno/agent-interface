# Post-merge measurement completeness correction — #3807

This note supplements the immutable formal result. It does not alter or replace `REPORT.md`, `FORMAL_RESULT.json`, `AUDIT.json`, `FREEZE.json`, or their hashes.

## Finding

- Frozen runner SHA-256: `43e6e6ef39883e78e50c3887b2ddf804a755f0305cad0d9ef6f640b00bdccdff`.
- The runner records 16 update durations for each online arm and per-seed final row-level expected labels/predictions for A, rank-2 online B, rank-4 online B, and rank-4 batch B.
- The online loop calls the update function once per arriving row but does not evaluate held-out accuracy after each arrival. Evaluation occurs only after all 16 feedback rows and updates are complete. There is no accuracy learning-curve field in the runner output or merged raw result.
- The rank-4 batch arm records a single batch duration; it has no incremental arrival evaluations by design.

## Disposition and scope

Secondary measurement-completeness status: **`HOLD_LEARNING_CURVE_NOT_RECORDED`** against Issue #3790's request to retain a learning curve.

The separately audited final-accuracy disposition remains **`FAIL_ONLINE_RANK_CAPACITY_GPU`** unchanged: its per-row final predictions and expected labels establish the final held-out metrics and their predeclared quality-gate misses. Route, snapshot and base-integrity audit results are unchanged. No cause for the rank-4 collapse is inferred.

The exact 41,257-byte merged stdout wrapper SHA-256 is `abf9a01dd4dc34bc137bf4c25d191372ddceb8c872b3df73a61cdc9c30defc06`; its canonical decompressed payload SHA-256 is `2ae484327db48fd1f428e2f724887edcdc06da771f0df97c5d2cfbda7a7d7bf0`.

This was a read-only code/artifact audit. No GPU or CPU model process, training, optimizer step, data regeneration, or evaluation was performed. Any learning-curve study requires a distinct future allocation and successor issue; it must not rewrite or rerun #3807.
