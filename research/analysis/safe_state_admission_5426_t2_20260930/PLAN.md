# Issue #5426 T2 — safe-state admission under claim error

## H / T / D / C / U

**H.** With truthful bounded maximum claims, prospective Banker admission can avoid an unsafe resource state without aborting a workflow; claim error, lease expiry, and shared-resource invalidation must invalidate the witness rather than preserve stale permission.

**T.** Freeze six deterministic traces over three unit-capacity resources and three workflows where used: safe interleaving, a two-workflow cycle, one overestimated claim, one post-admission underclaim expansion, lease expiry, and shared-resource generation invalidation. Compare per-resource quota, a reactive cycle/siphon guard (abort the requester that closes a wait cycle), Banker safe-state admission, and a global exclusive workflow lock. Use no RNG, model, GUI, external resource, or network. Retain all decisions and allocations; independently recompute safe-sequence witnesses, terminal wait cycles, completion counts, and invalidation handling.

**D.** A scoped PASS requires Banker to admit only states with an independent completion-sequence witness under truthful claims, detect/abort claim expansion before relying on the old witness, and outperform both quota and the reactive guard on the preregistered truthful cyclic trace without more aborts, while preserving greater concurrent resource use than global serialization. All expiry and shared-fault generations must release or invalidate affected allocations. Any unsafe Banker grant is FAIL; absence of a strict comparative advantage is FAIL/HOLD for the hypothesis, not a threshold change.

**C.** Quota can deadlock on a cycle. The reactive guard may avoid deadlock by aborting a participant; therefore equal deadlock counts can conceal a completion/abort trade-off. A global lock can complete every scripted job but suppress parallel use. Overestimated claims are conservative and may create false holds; underestimation invalidates the guarantee.

**U.** This is a finite, hand-authored state-machine construction, not evidence that real agent workflows provide truthful maximum claims, that resource classes are fungible, or that the policy improves production liveness/fairness. The siphon baseline is a minimal wait-for-cycle guard, not a reproduction of Issue #5410's simulator. The shared Docker/OrbStack lane has no exact assignment for this experiment, so this rung is host-only and does not claim container parity.

## Frozen model details

- Resources: `input_authority`, `verifier_slot`, `observation_slot`, capacity one each.
- A workflow completes only after its `finish` event and acquisition of its actual remaining vector; completion returns all held units.
- Banker safety uses the frozen maximum-claim vector and a deterministic lexicographic completion sequence. An explicit claim expansion beyond that vector aborts the workflow and releases its allocation.
- The siphon comparator records pending-request-to-holder edges. If a new wait closes a cycle, it aborts that request's workflow and releases the held vector; this avoids conflating cycle detection with automatic recovery.
- Expiry aborts/releases only the named workflow. Shared-fault invalidation increments that resource's generation and aborts every workflow holding it; no old-generation allocation may survive.
- Metrics: completion/abort counts, unrecovered wait cycles, Banker false holds against actual remaining demand, safe-witness coverage, peak simultaneous holders, and invalidation/release reconciliation. Wall-clock timing is not a metric.

## Frozen outcome label

`PASS_SAFE_STATE_COMPARISON_SCOPED` only if every D gate passes. Otherwise retain the exact per-trace evidence as `FAIL_COMPARATIVE_GATE` or `HOLD_INTEGRITY`, with no claim of general deadlock prevention. No reruns or post-result policy/trace changes under this T2 identity.
