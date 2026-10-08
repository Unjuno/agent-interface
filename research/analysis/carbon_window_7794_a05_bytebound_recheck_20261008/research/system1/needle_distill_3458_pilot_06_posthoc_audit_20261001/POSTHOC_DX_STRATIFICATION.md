# Post-hoc raw stratification — Needle Pilot-06 (not a new formal allocation)

This note re-reads the immutable `formal/formal-01/FORMAL_RESULT.json` from Issue #3869 allocation `needle-intent-distill-3458-pilot-06-isolated-shift-audit`. It does not rerun training, inference, Docker, seeds, or the allocated auditor. The formal result and every historical audit attempt remain unchanged.

## Provenance

- Formal raw SHA-256: `0878c39a68fe2abea218132b307ceff77df1e9a52291ba14186f2c8c423e37a7` (3,701,595 bytes).
- Existing corrected independent audit: `AUDIT_FINAL.json`, SHA-256 `8a922fce11fcbc0daa67683ddf84e21cd99344cef4598546f56dbb49c3fc458f`; it binds the raw hash and reports `errors: []`.
- Frozen label oracle: watch if confidence `<0.72` or not visible; otherwise CONTINUE iff `|dx|<0.06`, `|dy|<0.06`, and `|vx|+|vy|<0.12`; otherwise CORRECT.
- The initial independent reconstruction used PowerShell 7.5.4. A retained stdlib-only Python reproducer, `reconstruct.py`, now re-derives the frozen teacher labels from each raw feature vector, verifies the exact raw/audit SHA-256 bindings and zero audit errors, then groups CORRECT rows by fixed descriptive `|dx|` bands `[0.071,0.090)`, `[0.090,0.120)`, `[0.120,0.149)`. It counts raw proposal=`CORRECT`, null proposal (YIELD), and other accepted proposals; expected coverage is 3 seeds × 1,024 rows = 3,072. No model import or training occurs.

## H / T / D / C / U

- **H (diagnostic, post-hoc):** The severe synthetic CORRECT-shift miss may be concentrated nearer the action boundary; accepted CORRECT proposals may vary materially across the farther `|dx|` band by seed.
- **T:** Read only the three frozen seed outputs. Independent script derives labels from features and frozen teacher rule, applies fixed descriptive `|dx|` bins, and tallies correct proposal / YIELD / wrong non-YIELD proposal. It does not inspect training or change decisions. A second check verifies total rows and compares raw identity with the retained corrected audit.
- **D:** This is descriptive only, not a preregistered pass/fail gate. Reproducible per-band counts support a localization of the already-failed synthetic result, not a causal explanation or a new success criterion.
- **C:** The shift is a hand-authored synthetic teacher; model seed, covariates, and learned decision surfaces all vary. The post-hoc bins were not an independently held-out threshold experiment.
- **U:** No external/Astra labels, real observations, robust generalization, calibration, GUI/servo/task effect, or online-learning claim. Do not tune or promote the model based on these bins.

## Result

| Seed | `|dx|` band | n | CORRECT proposal | YIELD | Wrong proposal |
|---:|---|---:|---:|---:|---:|
| 3467 | 0.071-<0.090 | 266 | 0 | 43 | 223 |
| 3467 | 0.090-<0.120 | 407 | 8 | 67 | 332 |
| 3467 | 0.120-<0.149 | 351 | 149 | 73 | 129 |
| 3468 | 0.071-<0.090 | 241 | 0 | 56 | 185 |
| 3468 | 0.090-<0.120 | 395 | 0 | 72 | 323 |
| 3468 | 0.120-<0.149 | 388 | 21 | 82 | 285 |
| 3469 | 0.071-<0.090 | 221 | 0 | 37 | 184 |
| 3469 | 0.090-<0.120 | 420 | 21 | 85 | 314 |
| 3469 | 0.120-<0.149 | 383 | 227 | 77 | 79 |
Across the near-boundary band `[0.071,0.090)`, CORRECT proposals were **0/728**; in `[0.090,0.120)`, **29/1,222**; in `[0.120,0.149)`, **397/1,122**, with strong seed variation (high-band correct proposals: 149/351, 21/388, 227/383). These are raw-stratified counts; a wrong proposal is any accepted label other than CORRECT, including CONTINUE or WATCH.

The original formal outcome remains `FAIL_NEAR_BOUNDARY_SHIFT`: all three seeds miss the frozen shifted accuracy and CORRECT recall gates; all 1,536/1,536 explicit boundary rows yield. This post-hoc note does not replace the report or upgrade any claim. Any generalization test needs a new frozen external/independently authored label source and fresh allocation.
