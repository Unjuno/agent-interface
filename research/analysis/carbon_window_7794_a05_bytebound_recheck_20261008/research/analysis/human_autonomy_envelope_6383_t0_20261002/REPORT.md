# T0 result — Issue #6383

Allocation `HUMAN-AUTONOMY-ENVELOPE-6383-T0-20261002-02` completed its frozen synthetic method check in two separate WSLc containers. The candidate and independent raw-fixture auditor both exited 0. The auditor reconstructed all 10 checkpoints with no errors and returned `PASS_METHOD_SCOPED`.

The fixture, candidate, auditor, and preregistration hashes match `FREEZE.json`. No retry or source change occurred after freeze. Candidate and auditor logs, exit codes, outputs, image identity, and the integrity manifest are retained with this report.

This is a bounded synthetic display-fidelity result. It does not establish human comprehension, operational benefit, runtime/GUI behavior, or live authority correctness. No people, model, GUI, or input were involved. GPU was intentionally not requested because this deterministic fixture task has no GPU workload. WSLc warned that kernel/cgroup swap-limit support was unavailable; the configured `1g` memory value is not claimed as an enforced cap. Read-only root and PID limits were not available through this invocation.

The run's frozen source base was `1326813275f1b73349acafc7c7cbc221e687dbd1`; the pre-run start gate recorded live main `557c5afafd64541e5db1ee2635e661bb87ea44ee` and no path conflict. The earlier allocation-01 STOP is retained unchanged. Three already-exited containers belonging to another task were observed after execution and left untouched.

Issue #6383 remains open for any further rung or design work. This T0 result alone does not satisfy the issue's broader human-awareness objective.
