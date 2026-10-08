# Successor preregistration — Issue #732 async resident steering

Allocation: `resident-reactive-async-steering-732-rung2-successor-01-20260921`
Predecessor: `resident-reactive-async-steering-732-rung2-20260921`, HOLD_SOURCE_HASH_NOT_PROPAGATED; retained unchanged at [predecessor PR #3749](https://github.com/Unjuno/agent-interface/pull/3749).
This is a new allocation. No predecessor output is pooled or relabeled.
Branch: `research/resident-reactive-async-steering-732-rung2-successor-01-20260921`
Path: `research/coordination/resident_reactive_async_steering_732_rung2_successor_01/`
Base: current `main` at branch creation.
Formal execution has not started.

## H — hypothesis

The exact finite dispatcher contract from the predecessor can meet the same gates when the runner's frozen source digest is supplied through the process environment, as the frozen source requires. This successor tests only the source-pin propagation correction; the state space and semantics are unchanged.

## T — frozen target and procedure

Repeat exactly the predecessor's finite contract matrix: phases {RUNNING, PAUSED, REVOKED, YIELDED} × owners {FREE, RESIDENT, EXTERNAL} × commands {BOUNDED_UPDATE, PARALLEL_ONESHOT, SAME_RESOURCE_ONESHOT, RESUME, REVOKE, UNKNOWN} × generation-match × safe-point × bounds = **576** rows, plus the same stateful traces. Copy the exact candidate/oracle semantics; change only the allocation identifier and runner-source pin propagation. Source digest is read from environment variable `FROZEN_RUNNER_SHA256`; launch wrapper must set that environment variable before execution and assert fetched-source SHA equals the preregistered value. Run construction-only checks, then exactly one formal invocation. No retry or post-result tuning.

## D — decision

`PASS_ASYNC_STEERING_CONTRACT_SCOPED` only if the output embeds the exact frozen runner SHA; all 576 Cartesian cases independently recompute with exact counts; the stateful trace preserves all eight invariants; three naive negative controls expose stale-generation admission, off-safe-point overlap, and delayed revoke; and the independent audit reports zero errors. Any mismatch is FAIL; missing or incomplete integrity evidence is HOLD. A valid contract pass does not prove runtime concurrency.

## C — constraints

This successor isolates harness propagation only; no changes to model, state space, seeds, dispatcher semantics, expected results, or gates. Exact finite semantics are enumerated on Windows host in-memory using standard-library Python -B; no Docker/container, CUDA, model/provider, GUI, network, input, local files, or cache. Docker Desktop Linux-engine pipe remains absent and C: has 0 free bytes. This is not container/runtime evidence.

## U — limits

Same finite serialized-dispatch contract only. No real scheduler interleavings, mailbox delivery, runtime fairness, atomic OS input release, GUI effect, performance, LoRA, learning, role-network generalization, or skill transfer. A pass may only motivate a separate empirical runtime successor.
