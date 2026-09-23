# #1495 fixed-ROI translation characterization — retained execution stop

Task: `VISUAL-INVALIDATION-ROI-TRANSLATION-ENVELOPE-20260918-001`

Decision: **CHARACTERIZATION_EXECUTION_STOP_TIMEOUT_NO_RESULT**

Scientific disposition: **NONE** for the fixed-seed characterization.

## Why this task existed

The retained `research/visual_invalidation_discovery_v1/REPORT.md` explicitly named target motion relative to the declared ROI as its next smallest untested failure. #1495 preserved the predecessor detector constants and added only policy-permitted target translation.

Frozen detector:
- ROI 48x48;
- target 12x12;
- relevant intensity change +16;
- independent Gaussian jitter sigma2;
- changed pixel when absolute difference >=12;
- invalidation at >=100 changed ROI pixels.

## Excluded construction

Construction used a separate excluded seed and is not the fixed characterization result.

- independent sigma0 geometric rows: 150/150 exact, mismatches0;
- horizontal translation-only d=4: invalidation0/250; d=5:250/250;
- vertical d=4:0/250; d=5:250/250;
- diagonal d=2:0/250; d=3:250/250;
- relevant-change detection in all six boundary controls:250/250 each;
- independent formula audit: PASS.

This is PASS-shaped construction evidence that a finite direction-dependent drift boundary exists. It is not promoted to the preregistered characterization outcome.

## Source-first integrity

The first GitHub source upload differed byte-for-byte from the locally executed construction source for `experiment.py` and `independent_audit.py`. The characterization seed had not been used.

The remote source was corrected to the exact local construction-tested bytes, then re-read:
- `experiment.py` Git blob `849fa1f45e8d8af6ee0caadd0baa8f2e2a42b8d6`;
- `audit.py` Git blob `52b2e3fceae6e505d6ba42718f0ff346f9e2ba86`;
- `independent_audit.py` Git blob `69b8cb15b0c1f4a5a574fa73c8f1cda4ee1b6017`.

`SOURCE_FREEZE.json` records the full readback map. This pre-seed transfer defect is retained rather than hidden.

## Fixed-seed execution

After freeze and collision reread, seed `149420260918001` was started exactly once.

The full-canvas Monte Carlo implementation did not serialize `characterization.json` before the 300 second execution wrapper expired.

Post-stop checks:
- result file absent;
- audit file absent;
- independent audit file absent;
- residual experiment process0;
- reruns0 / replacements0 / tuning0.

Environment:
- CPython 3.13.5;
- NumPy 2.3.5;
- Linux 6.18.44 x86_64 / glibc2.41;
- 5 visible CPUs.

No partial scientific rows are pooled because the frozen runner serializes only after the full corpus.

## Interpretation

The task did **not** answer the preregistered translation-envelope characterization. It exposed an execution-harness inefficiency: each detector decision uses only a 48x48 ROI, but the frozen runner generates independent Gaussian noise across two full 256x256 canvases for every pair.

A legitimate successor may change only that execution representation, for example generate the mathematically equivalent ROI distribution directly or partition immutable cells. It must use a fresh allocation/seed and preserve all detector, geometry, nuisance and decision gates.

No X11, GUI, model, provider, task input or shared runtime was used.
