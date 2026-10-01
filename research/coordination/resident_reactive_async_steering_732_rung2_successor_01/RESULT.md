# Issue #732 Rung 2 successor — async steering contract

Allocation: `resident-reactive-async-steering-732-rung2-successor-01-20260921`
Disposition: **PASS_ASYNC_STEERING_CONTRACT_SCOPED**
Predecessor: [#3749 HOLD](https://github.com/Unjuno/agent-interface/pull/3749), preserved unchanged.
Branch: `research/resident-reactive-async-steering-732-rung2-successor-01-20260921`
Frozen source identities: [FREEZE.json](FREEZE.json)

## H / T / D

**H:** Generation-bound steering can preserve a bounded resident program when parameter updates wait for safe points, disjoint-resource one-shots remain nonconflicting, same-resource operations use explicit handoff, stale messages are rejected, and current-generation revoke releases immediately.

**T:** One exhaustive enumeration of 4 phases × 3 resource owners × 6 command types × 2 generation-match values × 2 safe-point values × 2 parameter-bound values, plus the frozen stateful trace.

**D:** All gates passed:
- **576/576** unique Cartesian states independently recomputed; zero errors.
- Outcome histogram exactly matched candidate and audit.
- **10/10** trace events matched; all **8/8** stateful invariants true.
- Stale-generation, off-safe-point overlap, and delayed-revoke negative controls all reproduced.
- Formal JSON embeds the exact frozen runner SHA-256; the frozen auditor SHA was checked before execution and its unchanged source reports PASS.

Full first output: [RESULT.json](RESULT.json). Independent audit: [AUDIT.json](AUDIT.json).

## Execution and limits

Exactly one formal enumeration ran in memory using Windows host Python 3.11.9 with `-B`, standard library only. No local files/cache, CUDA, model/provider, GUI, OS input, or application effect was used. This is an exact finite-contract analysis, not a Docker/container run or runtime-concurrency test. Docker Desktop's Linux engine pipe is absent and C: reports 0 free bytes; the modeled semantics are finite and do not depend on a real scheduler, so exhaustive analysis was the relevant first method.

This PASS establishes only agreement with the declared serialized-dispatch contract. It does not prove actual mailbox ordering, scheduler fairness, atomic OS input release, runtime implementation correctness, GUI/task effects, latency, learned adaptation, LoRA, role-network learning, or skill transfer. It supports a distinct empirical runtime successor only if/when the dispatcher implementation and a usable container/backend are available.

The predecessor's source-pin failure remains in its original result and PR; the successor changes only allocation identity and environment-based hash propagation, with unchanged state space and gates.
