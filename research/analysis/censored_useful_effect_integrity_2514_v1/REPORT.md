# #2514 censored useful-effect integrity repair

Decision: **PASS_CENSORED_USEFUL_EFFECT_INTEGRITY_REPAIRED**.

This is a fresh unique integrity allocation. It does not relabel #1964, PR #1971, or
PR #1990; their duplicate-allocation/vacuous-control history remains unchanged.

## Fixed semantics

Same #1964 finite domain and half-open membership contract:
- integer edge bounds 0..6;
- feasible worlds satisfy D<=R;
- effect is absent or -1..7;
- cause is ACTION or ENVIRONMENT;
- ACTION effect membership in [D,R) is T in every feasible world, F in none, U otherwise.

Only the integrity layer changed: unique allocation identity, independent world-enumerating
oracle, complete raw/result/oracle retention, and six byte-changing corruption controls.

## First outcome

- formal invocations: 1; reruns/replacements/tuning: 0/0/0
- edge domains: 658
- observations: 13,160
- candidate/oracle mismatches: 0
- counts: F=11,340; T=252; U=1,568
- exact-edge U: 0
- valid one-endpoint inward-refinement comparisons: 39,200
- malformed input rejections: 7/7
- opposite-label shared-observation witness: verified
- independent auditor imports no candidate helper
- tamper controls: 6/6 rejected and every mutation changed retained bytes
- formal exit 0 / audit exit 0 / stderr 0 bytes for both
- postformal frozen source rehash: 6/6 exact

Tamper rejection reasons: verdict→corpus/verdict mismatch; missing→corpus/verdict
mismatch; duplicate→duplicate; endpoint→corpus/verdict mismatch; total→total;
digest→digest. Non-digest raw mutations were rehashed before verification, so these are
not stale-hash-only controls.

## Evidence identities

- preformal source capsule SHA-256: `a458edc7d548e01ae02e1d9bf867511c16a8c83acf7ab664b1f26211cc0bced2`
- SOURCE_FREEZE SHA-256: `6ed034b1f7ce23f54f90288284f71ee08b67da7b678799225eb23169709fdb12`
- RAW SHA-256: `8c87575c522d1bf2efb8cac93a96a2e0973c88e4439c27dabae51bd462690bde`
- RESULT SHA-256: `ed64a33e14c75daacdfec3cf7e39fcf74e19dd9601719c9e8283c845163f89f2`
- ORACLE SHA-256: `706101c6fc8adb84776fa95c427fc4a5c1476fde402fb2f07db9dc2a3630d629`

## Scope

Synthetic finite same-clock semantic evidence only. No physical clock comparability,
causal-effect discovery, occupancy duration, GUI/X11/model/task efficacy, token, latency,
human-tempo or production claim. A PASS repairs the audit/integrity basis for this model;
it does not retroactively validate the historical #1971 formal claim.
