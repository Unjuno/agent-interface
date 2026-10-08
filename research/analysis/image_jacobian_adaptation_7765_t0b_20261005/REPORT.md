# Issue #7765 T0b — calibrated held-out result

**Disposition: `FAIL_NO_GAIN`.** The audited separate-seed calibration selected fixed gain 0.9. On the disjoint held-out drift/cross-coupling subset, calibrated fixed gain required 185 corrections and online Jacobian 191 (3.24% more for the adaptive arm), below the preregistered >=20% reduction. All 240 arm rows were independently reconstructed with zero errors; all goals were reached and matched; safety violations were zero. The frozen negative result is retained; no rerun or tuning followed.

## H/T/D/C/U

**H.** Online same-target Broyden/secant adaptation would reduce paired total corrections by at least 20% over a fixed gain calibrated on disjoint training seeds, without changing independently scored goals or safety.

**T.** Fixed gain 0.9 was selected and independently audited on 240 training rows using seeds 3000–3019. Held-out T0b then ran 30 seeds per condition for constant, gain drift, cross-coupling, and saturation (240 arm rows; seeds 4000–4029). Candidate and independent auditor each ran once on local CPython 3.14.5/macOS arm64. The runtime deviation (OrbStack content-store blob error) is documented; this simulation makes no host timing/resource claim.

**D.** Audit gate passed with zero errors; all goals matched and safety violations were zero. On the preregistered adaptation subset: fixed 185 vs online 191, reduction fraction −0.0324. Thus `FAIL_NO_GAIN`; do not promote the Jacobian adaptation hypothesis.

**C.** Matched held-out seeds, start state, action/observation constraints, independent hidden plant and terminal oracle. The fixed gain was selected only on disjoint calibration seeds; calibration A01's unaudited 0.9 selection was excluded. T0's unequal-gain result remains a separate confounded predecessor.

**U.** Finite authored 2-D plant and perfect feature oracle; no real GUI, delayed/occluded features, semantic task effect, human tempo, or broad transfer claim.

## Reproduction

Calibration result and source hashes are retained in sibling `image_jacobian_adaptation_7765_t0b_cal_a02_20261005/`. Held-out raw, audit, exit codes and receipts are under `formal_01/`. The candidate output is SHA-256 `b1b362d2fba8ed8e1d51bfdf3d9656659d11e86181c95c97d2adb7db1be6a4f7`. See `SHA256SUMS`; no candidate/auditor retry or post-run tuning was made.
