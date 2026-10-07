# A03 formal result — #6389

**Outcome: `PASS_COST_SCOPED`** (2026-10-04 UTC). The preregistered finite
comparison ran exactly once from commit `1bb01dd6`; no retries were made.

## Result

| Arm | Pair 1 (s) | Pair 2 (s) | Pair 3 (s) | Median (s) |
|---|---:|---:|---:|---:|
| Ubuntu WSL2 native | 1.140529 | 0.656410 | 0.810109 | 0.810109 |
| WSLc | 1.697851 | 1.512302 | 1.980227 | 1.697851 |

Native median end-to-end candidate-plus-independent-audit time was 52.29%
lower for this workload. All six candidate invocations and all six independent
auditor invocations exited 0. Across each of the six audits, the result was
`PASS_METHOD_SCOPED`, 9 rows received, zero unsafe admissions, zero errors,
and all 4/4 mutation controls detected. Candidate outputs were byte-identical
across arms and repetitions; all audit JSON outputs were byte-identical.

The WSLc runtime emitted `Your kernel does not support swap limit capabilities
or the cgroup is not mounted. Memory limited without swap.` Therefore `--memory
512M` remains a requested limit, not evidence of an effective enforced cap.
This result makes no claim about peak RSS, OOM prevention, pressure relief,
Docker comparison, GUI/model/GPU work, or repository-wide migration. Python
versions and libc differ between arms, and this small workload can magnify
startup overhead; three pairs do not characterize fleet-wide distributions.

The frozen main SHA matched immediately before candidate execution. Each WSLc
invocation recorded an empty running-container inventory and the exact pinned
image digest/local image ID. Raw outputs, receipts, event log, and audit
results are retained under [`formal/`](formal/); see `SHA256SUMS.txt` for the
evidence hashes. A01 and A02 first outcomes remain unchanged.
