# Issue #7712 T0 result

## Observed result

The one frozen candidate invocation completed on CPython 3.12.10 and returned all six declared cases. The independent auditor returned `PASS_METHOD_SCOPED` (six scoped checks). Four auditor tests passed, including three frozen mutation controls. The commands and exit codes are in `RUN.txt`; the exact outputs are `raw.json` and `audit.json`.

The result matches the declared `I_min` atoms: duplicate-source redundancy is 1 bit; X1-only and X2-only fixtures each have 1 bit unique information; XOR has 1 bit synergy; the independent null has zero information; and the imbalanced X1-only fixture has `H(Y)=0.8112781244591328` bits of X1-unique information. All atoms are nonnegative within the frozen tolerance.

## Decision

T0 passes for this exact discrete method and fixture set. A subsequent read-only T1 audit of retained #6678 browser-fixture data found all 72 same-capture modality bundles and an independently authored state oracle, but no independent safe-action/effect labels (`HOLD_NO_SAFE_ACTION_EFFECT_LABELS`). Thus those data can check channel pairing, but cannot supply the target required for #7712's proposed decision-conditioned PID/ablation claim. The exact inventory audit is in `t1_readonly_audit/`. T0 and T1 do not support an H-pass about natural GUI modalities or predict held-out ablation effects.

## Evidence and integrity

- Preregistration and frozen inputs/code: `PREREGISTRATION.md`, `fixture.json`, `candidate.py`, `audit.py`, and `test_audit.py`.
- Pre-execution input hashes: `SHA256SUMS.txt`.
- Raw candidate output, independent result, command log: `raw.json`, `audit.json`, `RUN.txt`.
- Post-run output hashes: `RESULT_SHA256SUMS.txt`.
- The source freeze was repository main `b67fc4f33a28f9cea1c4c6cb2d95a470f6be53f3`; main subsequently advanced by one documentation/evidence commit while this CPU-only fixture ran.

All declared hashes were rechecked after execution. No GUI, model, application, network, container, GPU, OS input, or formal allocation was used.
