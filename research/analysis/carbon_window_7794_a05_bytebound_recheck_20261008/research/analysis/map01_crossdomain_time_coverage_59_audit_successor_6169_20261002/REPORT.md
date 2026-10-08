# #6164 audit-only successor — result

Allocation: `R133-CROSSDOMAIN-TIME-COVERAGE-AUDIT-6169-20261002-01`

Source main: `f9633921c93530054b0d7320b1665df114050d52`

Predecessor PR #6164 immutable branch head: `edb62ea4f935c3bf987010623c6aa103306ce14e`

## Disposition

**`PASS_AUDIT_SUCCESSOR_SCOPED`.** The corrected independent raw-only audit ran once and accepted the unchanged #6164 candidate's `HOLD_CROSSDOMAIN_TIME_COVERAGE_UNIDENTIFIED`. The original #6164 audit `FAIL_AUDIT`, raw inputs, candidate output, and allocation are not modified or reclassified.

## Finding

The predecessor audit's fixed v38 fixture expected zero `post_control_score` rows, but the immutable v38 stream and candidate both contain one. The successor reconstructs and accepts that count. It also confirms the OpenTTD output's two separately defined cardinalities: `observer_records=1` is the single transition-witness row sent to the classifier, while `observer_record_count=263` is the full AIT stream length. The transition is at record index 91 across two unique states. The values 1 and 263 are not contradictory once their source semantics are traced; the predecessor report's “inconsistent counts” phrasing was too strong and should be read as an unverified concern, not a proven candidate defect.

Independent raw reconstruction:

- DOOM v38: 11 input admissions, 11 `keys_held`, 0 `input_released`, 1 `post_control_score`, no per-press-up witness.
- DOOM v39: 39 input admissions, 28 `keys_held`, 1 `input_released`, 1 `post_control_score`, no per-press-up witness.
- OpenTTD: 7 button-down admissions, 0 button-up admissions, 7 same-program verified-neutral terminal joins; 263 observer rows, two unique states and one transition at index 91.

All six historical source SHA-256 values, the predecessor FREEZE SHA-256, and candidate-result SHA-256 matched. Six construction tests passed, including rejection of a zero v38 score count, candidate/raw count drift, a forged observer transition index and raw-hash tampering. One Windows text-mode normalization defect was found in construction and fixed before the formal run; the final tests passed after the fix.

## H / T / D / C / U

- **H:** A distinct raw-only auditor can validate the predecessor's scoped HOLD after correcting the raw count expectation and checking candidate summaries against raw evidence.
- **T:** One corrected audit of the hash-bound predecessor candidate result and six immutable inputs; no predecessor candidate or auditor rerun and no live, model, game, GUI, input, or container execution.
- **D:** `audit_result.json` records the single formal audit; `RUN.json`, `FREEZE.json`, and hashes retain the invocation, source identities, controls and limits.
- **C:** PASS requires exact source identities, preserved candidate HOLD, raw/candidate count agreement, correct distinct observer cardinalities and rejection of all corruption controls. These gates passed.
- **U:** No physical key/button occupancy or common time denominator is identified. Useful-effect timing, cross-domain coverage, task value, latency, safety rate and MAP01 success remain unproven. Issue #59 remains open.

## Reproduction

After checking `FREEZE.json`: `python download_frozen_inputs.py`; `python -m unittest -v test_audit_successor.py`; then exactly once, `python audit_successor.py`. The downloaded files are ignored under `_run/`; hashes are in `FREEZE.json`. Do not rerun the formal auditor or alter the predecessor allocation.
