# Issue #7678 successor A02 — four-route retained result

**Formal disposition: `HOLD_AUDITOR_STARTUP_ERROR`.** The frozen candidate ran once and wrote 6,624 rows. Its one formal auditor invocation exited 1 before reconstruction because the dynamic loader omitted `__file__`. Neither candidate nor auditor was retried.

A separately versioned read-only audit reconstructed all 6,624 rows from the independent rank-vector oracle, finding 6,383 certificate-changing non-sincere reports and zero safe-beneficial reports under the preregistered utility in either information partition. It also found that the candidate cache key omits grants and protected constraints: the revoked-grant and protected-route controls therefore reused baseline certificates and failed the frozen D gate.

The precise raw evidence, initial failure, later audit versions, limitations, and artifact hashes remain in [the retained detailed result](results/a02/RESULT.md). This is a finite synthetic diagnostic only; it does not establish general strategyproofness or justify reducing transparency. A01 and the merged three-route A02 remain distinct and unchanged.
