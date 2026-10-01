# Successor allocation plan: 3442 intent-generation fencing T0 v2

Predecessor allocation 01 is retained unchanged except its additive STOP record: candidate exit 0, auditor syntax exit 1, raw capture incomplete, scientific result NOT_EVALUATED. No replay of allocation 01.

## H/T/D/C/U

H: In the finite event-order fixture, FENCE_RECONCILE blocks old-generation proposals after a delivered authenticated revision, cancels admitted/unemitted actions with verified release, preserves UNKNOWN for emitted/pending actions, preserves completed effects, and resists stale messages and generation reuse. Compare START_ONLY and atomic ADMISSION_FENCE.

T: Eleven frozen event traces x three policies = 33 rows. Each raw row carries the ordered event sequence, proposal/published/delivered tokens, delivery uncertainty, prior effect state, admission, emission, terminal effect, release and stale reactivation. Candidate stdout is captured as an in-memory string by the orchestration layer before any auditor call; write GitHub only after successful independent audit. Candidate once; separate raw-only auditor once. Four corruption controls. CPU-only synthetic method test; no task input, model, GUI or product effect.

D: PASS_METHOD_SCOPED iff exact 33 keys/event traces and independent policy invariants pass, stable progress is preserved, unsafe stale admission/re-activation is absent, pending physical effects remain UNKNOWN until receipt, already verified effects remain verified, uncertain delivery fails closed, and all 4 corruption mutations are rejected. Otherwise HOLD/FAIL. No live claim.

C: Deterministic fixture may encode its assumptions; actual auth, transport, broker atomicity, OS emission/release and semantic effect receipts are not tested. Existing leases/gates may suffice.

U: Finite abstract-method evidence only; no runtime integration, GUI safety, intent semantics, human benefit, latency or effect reliability.

Frozen base main: 5865c5e74842b5bba6a6291e141afae75ca4a147. Pinned Python host is 3.11.9; no files are written locally, Python -B. Docker Desktop remains open; docker info timed out and C: has 0 bytes free. No Docker/GPU invocation. Predecessor STOP path remains immutable.
