# T0 preregistration — Issue #5704

## Hypothesis and scope

Under a frozen finite one-crash model with fair reconciliation and responsive trusted release/fencing, every enumerated discordant internal state converges within six steps to `SAFE_QUIESCENT_UNKNOWN` with no stale/duplicate action admission. If the physical-release oracle is absent, the only acceptable result is `HOLD_UNKNOWN_INPUT`. `RESUMABLE_CURRENT` additionally requires independently readable effect status, current target, and fresh authorization; recovery never resends a previous claim.

## State space and test

The product contains 13,824 configurations: three planner/broker/actuator epoch bits; pending claim absent/present; delivery known/unknown; effect NONE/APPLIED/UNKNOWN; physical input RELEASED/HELD/UNKNOWN; release oracle available/unavailable; effect oracle available/unavailable; target CURRENT/STALE/UNKNOWN; fresh authorization absent/present; persisted authority absent/present. For every starting state, one crash/restart starts with volatile admission closed, advances one fence generation, and enumerates all 120 permutations of planner/broker/actuator synchronization, claim quarantine, and trusted release. Twelve unique message orders cover one duplicated old CLAIM interleaved with ACK and RELEASE_ACK. Old messages cannot grant authority or prove physical release. Compare unsafe naïve last-state resend, permanent STOP, and monotone fence/reconcile.

## H/T/D/C/U

- **H:** The reconciler has zero stale/duplicate admissions; every fair schedule reaches the safe quiescent set iff trusted release is responsive; missing release evidence remains HOLD; only fresh independent effect/target evidence and new authorization permit resumption. Naïve restore exposes a counterexample; permanent STOP remains non-admitting but fails the convergence bound.
- **T:** Exhaustive product-state candidate in `model.py`; separate raw-only checker in `audit.py`; enumerate every initial tuple, every fair local-step order, and all 12 delayed/duplicate/reordered message orders. Keep uncertainty and claims; do not infer an external effect or replay safety from internal state.
- **D:** `METHOD_PASS_SCOPED` only if all 13,824 states and 1,658,880 fair traces reconcile; every state has zero admission and six-step bound; exactly unavailable-release states do not reach quiescence; resumability gates are necessary; message orders produce no admission or forged release proof; naïve has unsafe counterexamples and permanent STOP never progresses. Any mismatch is `FAIL_METHOD`; absent source/slot/image/raw/audit evidence is `NOT_EVALUATED/STOP`.
- **C:** Authored finite model, not implementation code. The model assumes the trusted fence/release transition has the specified semantics.
- **U:** No arbitrary Byzantine behavior, real process/GUI, external effect oracle, physical release measurement, OS input or production reliability claim. Fairness and trust assumptions are explicit and narrow.

## Container allocation and image

Allocation `SAFE-RESTART-CONVERGENCE-5704-T0-ORB-20261001-01`; branch `research/self-stabilizing-restart-5704-t0-20261001`; frozen base main `150d5bd55d49f25830686eb529115405b08a7d59`. Requested local slot is 2026-10-01 05:25–05:50 UTC. No slot is assumed until the coordinator confirms it. Intended guest: Ubuntu 24.04, isolated networking and filesystem integration, 1 CPU, 2 GiB RAM, 16 GiB disk; a dedicated Docker daemon inside that guest only. Candidate and auditor are separate `--network none`, read-only-source, 1 CPU/512 MiB/64-PID containers. Do not inspect/use the shared OrbStack Docker context or its Created containers.

Image: `python:3.12-slim-bookworm@sha256:eb5be8e5b4d0a159c237946bbdd06356dda5d19c30fc4f7843e8046d3a590333`, linux/arm64/v8 (child of index digest `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`). Candidate once; independent auditor once after candidate exit 0. No retry or source change after freeze.
