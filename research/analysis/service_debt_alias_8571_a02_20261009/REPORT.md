# Issue #8571 A02 — five-request alias partitions

**Disposition: `PASS_METHOD_SCOPED`.** The allocation was frozen and committed before formal execution. The candidate and independent auditor each ran once; the auditor reconstructed all 177 rows with zero errors. Four construction tests passed before freeze, including all five mutation controls.

The one-identity presented-ID debt baseline allocated 2 service units each to A and B over a four-slot horizon. Across the complete set of 52 partitions of five A requests, 46 of 51 nontrivial alias partitions increased A's service share: 39 assigned A 3 slots and 7 assigned A all 4 slots. Five nontrivial partitions remained null and are retained. Trusted-parent debt reproduced the baseline trace in 52/52 partitions. FIFO's request order was identical in 52/52 partitions.

Equal-total-service fragmentation controls continued to allocate 2/2. The three genuinely distinct principals each received one dispatch. Revoked work remained excluded (A=0, B=4); missing-joint-grant work was excluded; the false parent assertion was rejected; mandatory release occurred at tick 2 after two one-tick jobs, with no later dispatch. Mutation controls cover revoked-work admission, release omission, false parent acceptance, forged useful-effect attribution, and altered timing.

This is a deterministic finite-method result with an authored trusted-parent mapping. It does not establish real alias/Sybil behavior, real-user fairness, identity provenance, semantic equivalence of service units, live GUI scheduling, or product benefit. A01 remains `HOLD_CUSTODY_FREEZE_NOT_COMMITTED_BEFORE_RUN`; A01 raw/audit were not reused or pooled.
