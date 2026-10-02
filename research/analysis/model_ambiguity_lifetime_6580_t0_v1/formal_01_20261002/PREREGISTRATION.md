# Issue #6580 T0 — preregistration

Allocation: `MODEL-AMBIGUITY-LIFETIME-6580-T0-20261002-01`  
Base main: `f891ccb0fabac44f43a0d05edfce5fac050e66f0`  
Branch: `research/model-ambiguity-lifetime-6580-t0-wslc-20261002`  
Status: preregistration only until its hash is recorded on Issue #6580. No formal candidate or auditor invocation has occurred at this point.

## H / T / D / C / U

**H.** A finite gate that represents the declared lifetime of uncertain transition variables and nature/agent move order explicitly can distinguish admissible continuation sets that are lost by a single lifetime-unspecified set, without making an in-envelope unsafe continuation. The null is that the tested distinctions do not alter any decision-relevant set or that the explicit gate adds no useful information.

**T.** T0 is a deterministic finite CPU-only enumeration. It covers (a) session/full stickiness, step/zero stickiness, and an event-triggered partial-stickiness rule on a named uncertainty variable; (b) nature-before-agent versus agent-before-nature choice on a one-step adversarial toy; (c) an observation-alias case, a negative control where all semantics coincide, and mutations that silently substitute one lifetime/order for another or narrow a set on a missing/stale receipt. An independent oracle, implemented separately from the candidate generator, reconstructs exact permitted uncertainty histories and safety dispositions. No GUI, model, human, GPU, network, input authority, or external effect.

**D.** `PASS_METHOD_SCOPED` only if all frozen positive-control distinguishability assertions and the negative control match the independent oracle, all candidate histories are exactly reconstructed, missing/stale evidence preserves the full uncertainty set, and every frozen mutation is rejected. Any unsafe in-envelope admission or oracle mismatch is `FAIL_METHOD`; missing/incomplete evidence is `HOLD`. This cannot establish that real interface dynamics have any tested lifetime/order.

**C.** Tiny deterministic finite automata do not reproduce general POSG/RPOMDP probabilities, stochastic observations, optimization, or app history. A gate could correctly preserve uncertainty but yield no useful action advantage. Runtime drift, hidden environment adaptation, and semantic effect verification are absent.

**U.** No GUI, real model, task-completion, safety, latency, token-saving, or real-world lifetime/order claim. T1 eligibility remains a separate read-only evidence audit; T2 requires separate authorization and allocation.

## Frozen fixture and methods

The candidate emits the Cartesian product of three lifetime rules × two move orders × two evidence states, plus a no-distinction control, and explicit witness histories. Each rule operates on a named binary uncertainty parameter over three transitions. Full stickiness fixes it at episode start; zero stickiness permits a fresh value per step; event stickiness allows the parameter to vary over the first two transitions, then fixes the second assignment after a declared event for the third. Agent-first/nature-first are represented as different information sets, not interchangeable labels. The control intentionally removes any downstream dependency on the parameter so all variants must agree.

The independent auditor reconstructs the allowed assignment sequences directly from this preregistered contract and verifies exact denominators. The construction suite applies seven frozen corruptions to copied fixtures: event commitment changed, zero stickiness silently collapsed to full, nature information set leaked across move order, responsive nature hidden from an agent-first move, missing/stale receipt narrows uncertainty, an expected row omitted, and an unsafe successor admitted. All synthetic effects are abstract `SAFE`/`UNSAFE` labels; no real action is run.

## Runtime and stop rule

Use native WSLc only: cached digest-pinned Python image, `--pull never`, `--network none`, one CPU, uid 65534, requested 1G. Record the exact kernel/cgroup warning and do not assert the memory limit is enforced. Construction, candidate, and independent auditor each have exactly one formal invocation; retain outputs/logs/exits and do not retry any stage. A mismatch or nonzero audit is retained as STOP/FAIL with no repair under this allocation.

## Provenance

Issue: https://github.com/Unjuno/agent-interface/issues/6580  
Image/runtime digest, source hashes, denominator, and empty output directory receipt are recorded in `FREEZE.json` before formal invocation.
