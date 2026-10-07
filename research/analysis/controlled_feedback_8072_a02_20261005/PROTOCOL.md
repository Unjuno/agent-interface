# #8072 T0 A02 — feedback-channel audit correction

**H:** In the authored finite world defined in A01, aggregate-only controlled feedback reduces development optimism relative to full feedback while retaining fresh utility within 0.05, with every planted hard-safety regression exactly disclosed and vetoed.

**T:** Fresh allocation `CONTROLLED-FEEDBACK-8072-A02-20261005-01`; 100 deterministic seeds, paired FULL/CONTROLLED arms, 16 development rows, 128 disjoint fresh rows, 8 proposals. A02 changes no hypothesis or simulator mechanics; its independent raw-only auditor additionally reconstructs serialized feedback on every query. Mutation controls forge feedback, alter task identity, omit a hard-failure disclosure, and claim a pre-lock fresh read. Candidate and auditor run once each in digest-pinned OrbStack Docker, network disabled and root filesystem read-only.

**D:** `PASS_METHOD_SCOPED` only if all candidate/feedback/acceptance/veto/query-order/final rows are reconstructed without errors; controlled median development-to-fresh optimism is lower than FULL; mean fresh utility is at most 0.05 lower; and all mutation controls are rejected. Else `FAIL_METHOD` or `HOLD_AUDIT`.

**C:** The hand-authored candidate family and update rules intentionally distinguish exact-ID memorization from stratum transfer. The threshold and behavior are not empirically fitted to researchers or real evaluation suites.

**U:** Synthetic method evidence only; no real researcher adaptation, GUI generalization, product requirement, privacy guarantee, or safety mechanism is established.
