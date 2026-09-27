# Runtime-owned currentness epoch barrier v1

TASK: CURRENTNESS-RUNTIME-EPOCH-BARRIER-20260918-002
BASE: 6a36c633e17f5910dc8c52661e3dbbc0cc010a52
PARENT: #1087

H: replace failed planner-generation magnitude comparison with a runtime-owned per-scope currentness epoch. Each unique invalidation increments the epoch; decisions are stamped at install; only equal-epoch decisions may execute.

T: standard-library container; fixed predecessor/adversarial controls; independent history-replay oracle; >=500,000 random transitions; bounded exhaustive traces.

D: zero stale-epoch admissions, planner generation has no semantic effect, duplicate invalidations no-op exactly once, duplicate decisions fail closed, cross-scope mutation zero, authority remains false.

C: hard epoch invalidation may be conservative even when an old policy remains semantically safe.

U: synthetic state semantics only; no planner/X11/task-performance claim.
