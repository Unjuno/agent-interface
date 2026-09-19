# Container revalidation of generation-bound evidence (#2166)

## Result

**PASS_CONTAINER_REVALIDATION_SCOPED**

The exact retained generation-bound harness from #2047 was copied to this additive successor path and executed once in `python:3.12-slim` with py_compile. Output digest matched the parent:

`9d4e4bb50d9ed35bfba829f17a3b34fd6790c4152f2c0e74a07af8aeb5f317b4`

Statuses were `ENCODED, OBSOLETE, CACHE_HIT, ENCODED`. Obsolete evidence had no bytes, exact-generation reuse was byte-identical, and the stale-unchecked control was rejected.

Counters: formal container=1, reruns=0, model=0, X11=0, task input=0.

## Boundary

This confirms container reproducibility and generation bookkeeping only. It does not establish PNG/X11 capture, model-facing value, latency, or task correctness. Parent #2047 and PR #2159 remain unchanged.
