# Recoverable X11 guard calibration A2 — retained construction failure

Issue #1777. Direct predecessor #1722 is the immutable formal execution stop.

## Disposition

**CONSTRUCTION_FAIL_BASELINE_SUBTRACTION_NONNEGATIVITY**

Formal0 / reruns0 / replacements0 / tuning0. This Task ID does not proceed to formal.

## One-factor success-envelope repair worked

A2 changed only the known-success observation envelope from20 ms to120 ms, while the stale no-effect envelope remained3 ms.

Excluded preflight:
- fresh correct-click success:128/128;
- fresh success observation max:1.150240 ms;
- stale cached click no-effect at3 ms:64/64;
- stale independent log noop→fallback-success:64/64;
- guard fresh false rejects0/64;
- guard stale false accepts0/64;
- terminal input neutral192/192.

Thus #1722's success-observation stop was not reproduced in A2 readiness testing.

## New construction failure

The inherited #1722 calibration source defines each group's baseline-subtracted costs and then requires the **minimum individual paired difference** for each cost family to be nonnegative.

A2 construction produced:

| quantity | mean | minimum | nonnegative samples |
|---|---:|---:|---:|
| c_y_stale | +3.691340 ms | -16.961574 ms | 11/12 |
| c_y_fresh | +3.344651 ms | -23.174477 ms | 11/12 |
| c_f | +11.138495 ms | -18.013156 ms | 11/12 |

The source therefore returns `FAIL_INTEGRITY` and the frozen-style primary auditor correctly returns `errors:["negative_cost"]`.

Recoverability, terminal input neutrality, guard classification and selector agreement on the resolved construction tiers all remained intact. Those facts do not override the failed construction gate.

## Diagnostic interpretation

The negative samples are matched wall-time differences, not physically negative operation durations. A paired baseline can be slower than its matched treatment because of scheduler/GUI noise.

The quantity in #1646 is an **expected incremental cost**. Requiring every noisy sample difference to be nonnegative is stronger than requiring the expected cost to be nonnegative and is not stable under timing noise.

Diagnostic paired-bootstrap intervals on the 12 construction differences:
- c_y_stale mean95%: approximately [-0.185,5.805] ms;
- c_y_fresh: [-1.590,5.959] ms;
- c_f: [2.626,21.628] ms.

These diagnostics were computed after the construction failure and are not promotion gates.

## Scope / next legal successor

Do not rerun #1777 and do not relax the gate inside this Task.

A fresh successor may change exactly one measurement rule: identify each cost as the expected paired increment and require a preregistered uncertainty criterion on that expectation, rather than requiring every individual paired difference to be nonnegative.

The successor must inherit unchanged:
-120 ms known-success envelope;
-3 ms stale-no-effect envelope;
-route/fixture/ROI;
-q tiers and formal corpus;
-baseline subtraction formulas;
-#1646 selector and held-out bootstrap policy comparison.

No production threshold, model/token, or general-GUI claim follows.
