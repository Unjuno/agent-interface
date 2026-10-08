# Issue #7501 MUS scaling boundary — A01

Status: frozen before candidate and auditor invocation. This additive T1/A01 does not modify the completed nine-case T0 package or its result.

Question: Does exact all-minimal-core enumeration retain a safe explicit `INCOMPLETE` boundary as the number of independent conflicts grows, and what is the subset-count cost on a deliberately constructed family?

Hypothesis: For `k` independent contradictory Boolean pairs, the candidate returns all `k` two-clause minimal cores and marks the row complete after exactly `2^(2k)-1` clause-subset checks when the budget covers the full family. When the budget is 1,024 checks and the full count exceeds budget, it returns `INCOMPLETE`, `complete=false`, `dispatch_allowed=false`; any partial core it emits is unsatisfiable and deletion-minimal.

Test: eight frozen deterministic rows with `k=1..6` complete budgets and `k=7,8` at budget 1,024. Each variable `x_i` has two source-distinct relaxable unit clauses `x_i` and `!x_i`. The independent audit enumerates assignments and clause subsets in integer-mask order, distinct from the candidate's cardinality-first combinations. For completed cases it compares the entire MUS set to the exhaustive oracle; for incomplete cases it validates each emitted partial core and the no-dispatch/incomplete disposition. Four mutations must be rejected.

Decision: PASS_SCALING_BOUNDARY only if all six complete cases return exactly `k` minimal cores at the exact `4^k-1` subset count, both budgeted cases stop at 1,024 with no dispatch and no false completeness, each emitted partial core is valid, and the auditor rejects all four mutations. Any mismatch is FAIL_METHOD; timeout/runtime or artifact failure before the candidate output is STOP_INFRA and is retained without retry.

Limits: This is a constructed Boolean family and direct code path, not arbitrary SAT/MUS scale, natural-language parsing, contract fidelity, user comprehension, solver performance generally, runtime authority, or effect safety. No GUI, model, GPU, human, external action, or production runtime code is used. No cgroup memory enforcement is claimed.
