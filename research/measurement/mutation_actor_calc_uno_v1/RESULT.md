# Result — #1251 Calc UNO actor attribution

Decision: **PASS_MUTATION_ACTOR_CALC_UNO_SCOPED**.

- Formal invocation: 1; reruns/replacements/tuning: 0.
- Real application substrate: isolated LibreOffice Calc, fresh profile, UNO named pipe.
- 180 formal cases = 9 frozen families × 20.
- Fresh injector children: 160; cleanup 160/160.
- Candidate / independent actor-oracle mismatch: 0.
- Lineage-bound non-self false self-credit: 0.
- Independent UNO scorer cell-readback errors: 0/180.
- Frozen <=500 ms TEMPORAL_NEAREST false self-credit: 140.
- States: SELF_CONFIRMED20 / EXTERNAL_CONFIRMED80 / UNATTRIBUTED60 / NO_MUTATION20.
- Authority promotions: 0; task-success promotions: 0.
- Action→independent Calc readback latency: median 64.920 ms, p95 71.819 ms, max 81.389 ms.
- Raw rows SHA-256: `836aa9362e4676b575e24e36041d92f1e0d08c352fad8776a78a60259ce6d11e`.
- Independent retained-row audit: PASS.

LibreOffice exits with code255 after the harness deliberately terminates the isolated process after document close; no UNO runner/scorer exception or child-cleanup loss occurred. This proves only controlled real-application composition through UNO. It does not establish provenance for generic pointer/keyboard input or authenticated human/OS actors.
