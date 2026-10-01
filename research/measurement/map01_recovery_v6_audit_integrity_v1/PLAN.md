# MAP01 recovery v6 audit-integrity preflight — Issue #1609

Task: `MAP01-RECOVERY-V6-AUDIT-INTEGRITY-20260918-001`.

## Roadmap
1. Bind current-main v4 base-audit and v6 wrapper-audit bytes by Git blob SHA.
2. Build a six-arm synthetic artifact whose arm-level evidence is internally valid and whose truthful pair summary is derived from those arms.
3. Freeze the probe, independent result auditor, and additive binding-guard candidate before the first exact-source decision test.
4. Execute one deterministic block against the exact retained audit source: truthful summary, summary-only corrupted decision inputs, invalid-arm control, wrong-boundary control.
5. Require identical non-summary tree bytes between truthful and summary-corrupt cases.
6. Retain first outcome; if confirmed, keep v6 live allocation unconsumed and publish the smallest additive audit-binding repair candidate only.

## H / T / D / C / U

**H.** With all six arm summaries/runtime evidence fixed, changing only pair-level `coast_no_retained_input_upper_ns` / `recovery_no_retained_input_upper_ns` in `summary.json` can change the retained v6 audit's HOLD/PASS_MECHANISM_ONLY decision without a hard failure.

**T.** Byte-bind exact retained audits; static source check for summary/arm numeric binding; deterministic six-arm artifact; exact-source audit on truthful and summary-only-corrupt trees; negative controls for invalid input evidence and wrong v6 planner-end phase; independent result audit. No live allocation.

**D.** `CONFIRMED_V6_SUMMARY_ARM_BINDING_GAP` iff truthful and corrupt trees have identical bytes outside `summary.json`, both are `valid_experiment=true`, scientific decisions differ across the frozen 10% gate, and the retained audit emits no summary/arm mismatch hard failure. `REFUTED...` iff retained audit detects the mismatch or decision cannot be changed. Source/control failures are `FAIL_INTEGRITY`.

**C.** Honest runner generation may create a correct `summary.json`; external artifact hashing can detect later byte tampering. The narrower question here is whether the retained audit *independently reconstructs* the numeric decision inputs from arm evidence.

**U.** Synthetic artifact-integrity evidence only. It says nothing about actual v6 recovery efficacy, real MAP01 timing, useful gameplay effect, or whether an attacker exists.

## Variables / fields

| Name | Meaning | SI unit | Definition | Domain / premise | Type |
|---|---|---|---|---|---|
| `C_i` | pair `i` coast no-retained-input upper bound | s (stored integer ns) | pair summary / coast arm input bound | `>0` | scalar integer |
| `R_i` | pair `i` recovery no-retained-input upper bound | s (stored integer ns) | pair summary / recovery arm input bound | `>=0` | scalar integer |
| `r_i` | pair continuity reduction fraction | dimensionless | `(C_i-R_i)/C_i` | `C_i>0` | scalar real |
| `m` | median paired reduction | dimensionless | median of three `r_i` | three pairs | scalar real |

Dimensional check: `C_i-R_i` and `C_i` are both time, so `r_i` is dimensionless; the frozen 0.10 threshold is dimensionless.
