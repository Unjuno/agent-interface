# Frozen analysis preregistration — Issue #732 async resident steering, rung 2

Allocation: `resident-reactive-async-steering-732-rung2-20260921`
Base: `main` at branch creation
Branch: `research/resident-reactive-async-steering-732-rung2-20260921`
Path: `research/coordination/resident_reactive_async_steering_732_rung2_v1/`
Formal execution has not started.

## H — hypothesis

A generation-bound resident reactive program can accept bounded planner steering without losing resource safety if parameter updates apply only at declared safe points, independent-resource one-shots remain nonconflicting, same-resource commands wait for or use an explicit pause/handoff, delayed old-generation commands are rejected, and current-generation revoke releases immediately without waiting for a safe point.

## T — frozen target and method

This is an exact finite transition-contract analysis of the next rung described in Issue #732 after `PASS_RESIDENT_REACTIVE_SIMULATED_INFERENCE_SCOPED`. It does not simulate OS scheduling or GUI behavior.

- Enumerate the full Cartesian product of: phase {RUNNING, PAUSED, REVOKED, YIELDED}; requested-resource owner {FREE, RESIDENT, EXTERNAL}; command {BOUNDED_UPDATE, NONCONFLICTING_ONESHOT, SAME_RESOURCE_ONESHOT, RESUME, REVOKE, UNKNOWN}; generation match {yes,no}; safe point {yes,no}; parameter in bounds {yes,no}. Total: 576 cases.
- Compare one frozen candidate dispatcher with an independently implemented declarative decision oracle for every row.
- Include explicit stateful traces for: deferred update then safe-point apply; keyboard one-shot while pointer remains resident-owned; conflicting pointer one-shot queued then safe-point handoff; generation advance then delayed stale command; stale revoke vs current immediate revoke; post-revoke command; and parameter-bound rejection.
- Retain candidate and oracle outcome per row plus stateful traces and negative-control outcomes.
- Standard-library Python only; no model, provider, GUI, input, network or CUDA. Host in-memory execution; no files or caches. This is analytical/enumerative evidence, not container evidence.

## D — decision

`PASS_ASYNC_STEERING_CONTRACT_SCOPED` only if the independent oracle matches the candidate for all 576 combinations and all stateful traces preserve:
1. no stale-generation command changes current state;
2. no out-of-bounds parameter applies and accepted update waits until safe point;
3. a nonconflicting one-shot does not relinquish resident pointer ownership;
4. same-resource action never overlaps resident ownership and is admitted only after safe-point handoff;
5. current-generation revoke releases immediately even off safe point; stale-generation revoke cannot affect the current program;
6. no command after REVOKED returns to an actionable phase;
7. baseline negative controls demonstrate stale-generation admission, unsafe off-safe-point same-resource overlap, and delayed revoke.

Any mismatch is FAIL. Missing rows, malformed evidence, or unverified source identity is HOLD.

## C — constraints and competing explanations

The analyzed state space is a declared finite contract, not real concurrency. It assumes a single serialized dispatcher, atomic state transitions, exact generation identifiers and accurate resource ownership. If real runtime mailbox scheduling, OS input release, crash/restart, or a non-atomic backend matters, exhaustive contract agreement is insufficient and requires a separate empirical successor. Docker Desktop Linux engine is unavailable (named pipe missing); C: has 0 free bytes. The chosen finite semantic question is tractable without a container under the repository's analysis-first method.

## U — limits

No implementation/runtime behavior, scheduler fairness, real planner latency, GUI effect, continuous control, throughput, real-time update, adapter/LoRA, role-network learning, skill transfer, or task-success claim. A PASS is only a bounded transition-contract result and justifies a separate runtime test only if empirical uncertainty remains.
