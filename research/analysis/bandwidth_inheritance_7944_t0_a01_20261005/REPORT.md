# Issue #7944 T0 A01 — result

**Disposition: `PASS_METHOD_SCOPED`; hypothesis: `H_PASS_SCOPED`.** This is exact behavior for the frozen authored model only. The candidate and raw-only auditor each ran once, both exited 0, and retries were zero. The auditor independently reconstructed all 27 policy/case traces (63 CPU execution events) with no errors.

## Result

| Frozen case | `NONE` | `PI_HOME_CHARGED` | `BWI` | Interpretation |
|---|---:|---:|---:|---|
| Budget inversion verifier completion | 8 (miss; deadline 4) | 8 (miss; deadline 4) | 2 (fresh; deadline 4) | Frozen hypothesis passes on its preregistered discriminator. BWI charges one holder tick to W, then the verifier uses W's remaining tick. |
| No contention verifier completion | 1 | 1 | 1 | Full event/outcome records are identical across arms; no inherited service. |
| Waiter budget exhausted during inheritance | 14 (miss) | 14 (miss) | 8 (miss) | BWI donates exactly one tick, exhausts W's initial budget, and does not promise a deadline when critical work exceeds available service. |
| Unlock at replenishment boundary | 5 (meets deadline 5) | 5 (meets deadline 5) | 4 (meets deadline 5) | Boundary ordering is explicit; BWI uses its initially available tick and the replenished waiter budget after unlock. |
| Two waiters | both miss | both miss | waiter1 misses; waiter2 completes at 2 | Only waiter1's single initial budget tick is charged; the result exposes a real trade-off rather than a uniform benefit. |
| Nested acyclic chain verifier | 9 (miss; deadline 4) | 9 (miss; deadline 4) | 3 (fresh; deadline 4) | Two critical-section ticks propagate from the waiter through the chain, then the verifier runs on its remaining W budget. |
| Dependency cycle / cancelled waiter / remote non-preemptible wait | no inheritance | no inheritance | no inheritance | Cycles are refused; cancellation and unsupported resource types do not donate. |

Across every frozen input, admitted server bandwidth sums to at most one CPU, every executed tick consumes exactly one server tick, and the raw trace contains no duplicated or refunded service. The five independent raw corruptions (budget refund, duplicate service, wrong charge server, stale freshness admission, omitted arm) were all rejected. Five separately reconstructed forged/stale/incomplete/remote-or-nonpreemptible/expired-edge controls produced zero inherited ticks and `UNKNOWN_STALE`.

`H_PASS_SCOPED` means only that the one preregistered budget-inversion witness and no-contention control behaved as predicted. The two-waiter and insufficient-waiter-budget cases demonstrate that BWI does not solve all contention and may leave one verifier stale. This finite result does not establish that BWI is generally preferable to bounded PI.

## Formal commands and immutable evidence

Construction checks passed 12/12 before freeze. They first caught an absent implementation and then a nested-chain wakeup defect; both were resolved before the allocation freeze. Those were pre-freeze construction outcomes, not formal candidate retries.

Frozen base main: `6860b585305e539ec93896f5adcbf658cbbd8592`. Freeze UTC: `2026-10-05T04:28:48Z`. `FREEZE.json` SHA-256: `bcba2cf99e818675c8c1c314a6c10404b6a5f333cf9dceedea125ddff819d17e`. All nine source/input bindings matched immediately before formal execution.

Candidate (one invocation, exit 0):

```sh
python3 -B research/analysis/bandwidth_inheritance_7944_t0_a01_20261005/candidate.py --output research/analysis/bandwidth_inheritance_7944_t0_a01_20261005/results/candidate.raw.json
```

Raw candidate SHA-256: `df298a45b024f4e9d513eb4ecc92c2dcca9a3542c1a7032928cdbc9c4576e576`.

Independent raw-only auditor (one invocation, exit 0):

```sh
python3 -B research/analysis/bandwidth_inheritance_7944_t0_a01_20261005/audit.py --raw research/analysis/bandwidth_inheritance_7944_t0_a01_20261005/results/candidate.raw.json --output research/analysis/bandwidth_inheritance_7944_t0_a01_20261005/results/AUDIT.json
```

Audit SHA-256: `3704a913f89d75639561b3687e5c94148fc97741f97b27847b391028037a3124`. Construction, raw output and auditor result remain separate; the formal candidate was not rerun during audit.

## Environment and claim limits

OrbStack Docker API was reachable, but image inventory and pinned `python:3.12-slim` execution failed on containerd content blobs with `operation not supported`. No container was created; no image/daemon repair was attempted. The pure standard-library model ran host-only on macOS 27.0.1 arm64 / CPython 3.14.5. No isolation, cgroup, swap, or resource-enforcement result is claimed.

The server model uses fixed `(Q,P)`, a fixed absolute deadline and replenishment only after budget exhaustion at that deadline. It is a small CBS-like contract, not full CBS. No general schedulability theorem, Agent Interface resource correspondence, implementation, host timing, GUI, model, user, task, latency, safety, or physical-input/release claim follows. Candidate and auditor are separately written by the same agent, not independent human review.

See [Issue #7979](https://github.com/Unjuno/agent-interface/issues/7979) for the allocation and result trail; parent [Issue #7944](https://github.com/Unjuno/agent-interface/issues/7944) is unchanged.
