# #1765 Independent raw audit of #1737 calibration fixture

Decision: **PASS_EVIDENCE_COMPUTE_CALIBRATION_FIXTURE_RAW_AUDIT_SCOPED**.

This successor does not rerun #1737 and does not change #1737's retained `FAIL_INTEGRITY / scientific NONE` disposition. It audits the exact first raw allocation already retained on main.

## Independent binding repair

The successor auditor does not import the #1737 runner or auditor and does not consume the predecessor `RESULT.json` aggregates. It independently reimplements the deterministic 8 MiB / 64 KiB / four-round SHA-256 digest oracle and reconstructs every active-row cost from primitive evidence:

`cost_ns = completion_wall_ns + obsolete_cpu_ns`.

Stored `cost_ns` must equal this reconstruction exactly. The corruption that defeated the predecessor audit — adding obsolete CPU a second time to stored cost — is now rejected. A separate primitive-completion mutation without updating cost is also rejected.

## Reconstructed first-raw result

From the exact retained RAW SHA-256 `71e9a44f02e86d498c567cd4286f6171e8472dee9e469fce7a7716b345d4f468`:

- active rows: 128 = 64 matched RUN/WAIT scenarios;
- frozen workload: 48 STABLE / 16 INVALIDATE;
- current-version digest: 128/128 correct;
- stale publications: 0;
- invalidated RUN old computation aborted: 16/16;
- invalidated RUN positive obsolete CPU: 16/16;
- authored workload invalidation incidence: 16/64 = 1/4;
- stable conditional WAIT loss `g`: 240,512,261 ns / 48 = 5.010672104 ms mean;
- invalidation conditional RUN waste `w`: 76,075,399 ns / 16 = 4.754712438 ms mean;
- measured fixture threshold `p* = g/(g+w) = 3,848,196,176 / 7,499,815,328 ≈ 0.51310546`;
- authored p=0.25 is below the threshold, so the scoped #1695 selector predicts RUN;
- reconstructed total RUN cost: 1,686,444,137 ns;
- reconstructed total WAIT cost: 1,850,880,999 ns;
- RUN advantage under the frozen utility: 164.436862 ms;
- exact identity `RUN-WAIT = w_sum-g_sum`: -164,436,862 ns;
- cache dispositions: 48 REUSE / 8 REBUILD_REQUIRED / 8 DROP_EXPIRED;
- authored fixture reuse rate: 48/64 = 3/4;
- retained version-check summary: 240,000 rows, p50 90 ns, p95 100 ns, max 253,594 ns.

All seven successor corruption/independence controls pass, including predecessor-RESULT irrelevance. Formal retained-audit invocation1; reruns/replacements/tuning0.

## Interpretation boundary

The successor repairs the evidence binding for the exact first RAW outcome only. It does not make the original #1737 auditor pass and does not erase that audit failure. The workload p=1/4 and reuse=3/4 are authored fixture frequencies, not deployment estimates. The utility gives one nanosecond of completion delay the same weight as one nanosecond of obsolete CPU; different utility weights change the break-even. Absolute timings are specific to this host and synthetic digest job.

The useful result is narrower: the #1702/#1695 decision lattice can be calibrated end-to-end in one explicitly defined job population when primitive evidence and derived costs are independently bound.
