# #6590 corrected T1: OrbStack formal result

## Decision

**`H_FAIL_SCOPED`** for the frozen synthetic position-random versus spatial-block discriminator. The independent audit reports zero integrity errors, and all preregistered competence, false-ACCEPT and block-support gates pass. The treatment gap is below the 0.20 threshold: position-random 1,218/2,560 = 0.475781; spatial-block 1,119/2,560 = 0.437109; absolute difference 99/2,560 = **0.038672**. Therefore this allocation does not support the hypothesis that random-position evaluation overstates block extrapolation by at least 20 percentage points. It does not establish equivalence or absence of other spatial structure.

## Execution and audit

- Issue #6590, allocation `spatial-block-position-6590-t1-orbstack-20261002-03`; source/freeze bound in `FREEZE.json`.
- Construction allocation `spatial-block-position-6590-t1-training-parity-20261002-03`: one network-none pinned OrbStack container; 9/9 tests pass. The corrected candidate and independently implemented auditor each fit the same 160-row construction input once; W1 changes and all four parameter arrays match byte-for-byte.
- Formal candidate: one distinct network-none OrbStack container, 10 fits over fresh seeds 659101–659105; exit 0. Independent auditor: one separate container, 10 independent refits; exit 0. Retries/replacements: zero. Runtime is about 15 seconds per formal container.
- Auditor reconstructed all 30,720 predictions and ten models with **zero errors**. Candidate raw SHA manifest covers 15 files, including predictions, manifests, receipts, environment and ten saved weight files; all 15 entries verify.
- Both arms base positive ACCEPT: 2,560/2,560 each (1.0). False ACCEPT: 0/2,560 negatives in every arm/cohort. Each spatial quadrant has 16 centers and 128 positive rows per seed, exceeding the frozen 8-center/100-row support minima.

## Seed-level treatment contrasts

| Seed | Position-random ACCEPT | Spatial-block ACCEPT | Difference |
|---|---:|---:|---:|
| 659101 | 0.5977 | 0.4844 | 0.1133 |
| 659102 | 0.5234 | 0.5156 | 0.0078 |
| 659103 | 0.2324 | 0.1719 | 0.0605 |
| 659104 | 0.8945 | 0.8535 | 0.0410 |
| 659105 | 0.1309 | 0.1602 | -0.0293 |

## Scope and preservation

This is one five-seed synthetic renderer allocation. Random and block cohorts are distinct interpolation/extrapolation envelopes; their observed difference is not estimator bias. It says nothing about production GUI spatial autocorrelation, real-layout robustness, safety, authority or product utility. The v1 `HOLD_AUDIT_INTEGRITY`, both v2 prelaunch STOP records, #4752's scoped PASS and previous #6590 geometry HOLD remain unchanged. The exact run, candidate raw, independent audit, container logs/inspects and hashes are retained under `results/`.
