# Issue #6156 — finite escrow rights protocol (T0)

## H / T / D / C / U

- **H:** With a fixed budget of four fungible optional units and two workers, preallocation can preserve the global cap while reducing per-use coordination in balanced demand. Under skew or uncertain crash recovery, conservative escrow strands rights and may complete fewer useful optional units than central admission.
- **T:** No-model finite-state-machine, budget B=4, two workers A/B, two generation-0 rights each, bounded operation sequences of depth 6. Enumerate enabled consume, crash, restart, heartbeat-reclaim, fenced surrender, and transfer-ack transitions. Independently regenerate the entire reachable-state and transition sets. Controls cover balanced/skew demand, crash with unavailable surrender, old-generation replay, duplicated/delayed transfer ACK, the heartbeat-reclaim overspend counterexample, optional exhaustion with mandatory verification, and ambiguous/self-reported work classification.
- **D:** PASS_METHOD_SCOPED only if the independent implementation exactly matches every state/edge, no reachable state violates right identity/conservation or permits stale use, all planted corruptions are detected, balanced demand keeps all four completions with 2 setup coordination round trips vs 4 central per-use checks, and the skew/crash cases expose stranded-right cost. Mandatory verification must never depend on optional rights; stale evidence requires a separate verifier or YIELD; ambiguous role is HOLD.
- **C:** Batched central admission may be simpler/equally fast; stranded rights after crash may dominate coordination savings; demand skew can waste allocated capacity.
- **U:** This is bounded enumeration of this abstract protocol, not proof of an arbitrary distributed implementation. It assumes a single issuer, durable consumed-right journal, true fungibility, unique transfer IDs, and correct generation fencing. It measures modeled coordination counts, not elapsed time. No GUI action authority, live workload, model, or product-speed claim.

## Frozen protocol semantics

There are exactly four unique rights, two initially held by A and two by B at generation 0. A right is in exactly one of HELD, CONSUMED, or IN_TRANSFER. Consumption is once-only, durable, and bound to owner plus generation. Crash alone and heartbeat timeout never return rights. A live current-generation holder may surrender a still-held right; the transfer uses a monotone unique transfer ID and remains in transfer until acknowledged. An acknowledged ID is idempotent forever; a delayed ACK for an older transfer cannot acknowledge a later transfer of the same right. Restart increments generation; old held rights remain stranded, and old tickets cannot consume or surrender them. No self-service generation refresh or speculative reissue exists.

Mandatory verification is an independent lane outside the optional numeric budget. Contract/event history, not the worker's self-label, determines work type. A stale observation requires mandatory verification; a routine discretionary recapture remains optional; ambiguous classification returns HOLD_ROLE_AMBIGUOUS. If mandatory service is unavailable, disposition is YIELD and consequential action is blocked.

The unsafe comparison mutant reissues a possibly consumed right on heartbeat timeout while the original durable receipt is delayed: B=4 with four original optional consumes plus a reissued fifth consume exceeds the cap. This is a deliberately planted protocol failure, not an observed external incident.

## Allocation and invocation

This is a fresh T0 for open Issue #6156. It does not alter predecessor evidence or claim T1. Freeze candidate, auditor, tests, protocol, container image and invocation before formal candidate/auditor runs. Run candidate once and the independent auditor once in digest-pinned, network-disabled containers. Preserve all raw outcomes; no retry.
