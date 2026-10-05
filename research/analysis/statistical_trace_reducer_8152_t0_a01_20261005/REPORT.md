# Issue #8152 T0 A01 result — PASS_METHOD_SCOPED

The independent raw-only auditor reconstructed the candidate output with zero errors. On this frozen synthetic trace fixture, sequential screening used 300 search replays versus 480 for fixed repetition, a reduction of 180 (37.5%). Both fixed and sequential final traces passed the disjoint held-out noninferiority rule. The one-run reducer accepted removal of `CORE_B` after a single rare matching outcome; its held-out target fingerprint occurred 13/200 times versus 145/200 for its independent baseline, and it failed noninferiority.

The result supports only the finite method comparison and this authored fixture. It is not evidence that a real interface trace is flaky or reducible, or that the method is safe, useful, causal, minimal, or calibrated on real failures.

## Frozen gates and independent checks

- Allocation: `UNJUNO-8152-STAT-TRACE-A01-20261005`, frozen source commit `89283d3d0e46ae916f8c452b4942a70c0170ac53`.
- Candidate and auditor each ran once in separate network-isolated OrbStack containers; both exited 0. Retries: 0.
- Candidate raw: 110,952 bytes, SHA-256 `42da11a224a0d4bce92329c3abde0ee1b402ff6dc8cf4661bcaebb9199880a82`. The auditor input copy has the same byte count and digest.
- Independent audit: `PASS_METHOD_SCOPED`, errors `[]`; audit JSON SHA-256 `f46f6ccd057356e9229c52004ab46bd99acef510e660a143b983540327030079`.
- Fixed search: 480 total replay queries; held-out baseline 136/200 and candidate 189/200; conservative lower difference bound 0.136822.
- Sequential search: 300 total replay queries; held-out baseline 138/200 and candidate 183/200; conservative lower difference bound 0.090115. The bound exceeds the frozen `-0.25` noninferiority floor.
- Single-run search: 6 total queries; final trace omitted `CORE_B`; held-out baseline 145/200 and candidate 13/200; lower difference bound `-0.767416`, so noninferiority fails.
- All six controls were detected: dropping authority, dropping release, same-exit-code competing fingerprint, search/confirmation seed overlap, missing raw row, and missingness treated as zero.
- Exact one-sided Clopper–Pearson interval coverage was independently reconstructed on p=0.01..0.99. Minimum fixed interval coverage was 0.990317 against the 0.99 per-interval bound. Sequential minima were 0.997628–0.998012 against 0.9975 per-look bounds; Bonferroni spending gives a 0.01 per-candidate union bound across four looks.

## Limits

The event plant is deterministic given SHA-256-derived trial identifiers and frozen trace contents; the Bernoulli interpretation is the authored synthetic sampling model. Confidence statements are conditional on that model and do not establish real-world calibration or stationarity. `AUTH`, `SETUP`, and `RELEASE` remain deterministic invariants and are never averaged. The run requested one CPU but did not independently verify cgroup enforcement; no memory cap is claimed. No GUI, model, retained failure, user data, network, or external action was involved.

See `PLAN.md`, `FREEZE.json`, `frozen/SHA256SUMS`, and `results/a01/RUN.json` for the protocol, identities, commands, raw, and receipts.
