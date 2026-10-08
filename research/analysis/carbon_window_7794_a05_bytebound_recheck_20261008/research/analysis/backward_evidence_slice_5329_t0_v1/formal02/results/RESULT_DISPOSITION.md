# Formal02 result: PASS_METHOD_SCOPED

Formal02 completed on the frozen four-case finite dependency graph. The
independent raw-only auditor returned `errors=[]`; all four preregistered
corruptions were rejected. Raw SHA-256:
`4693518956f2337ac7f9ae2134085c6df9069f498861c889b37935ef40acd16d`.

| Case | Oracle | Label-only | Data slice | Typed slice | Raw nodes | Typed nodes |
|---|---|---|---|---|---:|---:|
| clean + 12 irrelevant events | PASS | PASS | UNKNOWN | PASS | 19 | 7 |
| stale generation | STALE | PASS | UNKNOWN | STALE | 11 | 7 |
| verifier skipped/control branch | CONTRADICTED_OR_UNCHECKED | PASS | UNKNOWN | CONTRADICTED_OR_UNCHECKED | 11 | 8 |
| unresolved external cause | UNKNOWN | PASS | UNKNOWN | UNKNOWN | 9 | 8 |

On the clean/noise case, the typed slice retained 7/19 nodes (63.2% fewer
graph nodes; not a byte/token/latency measurement). It preserved the declared
decision across all four authored cases. Label-only produced false PASS on
three cases. The data-only policy abstained as UNKNOWN where required typed
predicates were absent; it did not silently infer a PASS.

Formal01 remains separately and unchanged `STOP_PROVENANCE_OR_RUNNER` because
its frozen auditor failed on a dangling unknown-cause edge. Formal02 is a new
allocation with a separately frozen auditor that treats unresolved targets as
explicit leaf sentinels. No Formal01 artifact was reused as a Formal02 result.

Scope: authored finite graph/truth table only. This is not evidence that real
GUI dependency graphs are complete, that backward slicing captures exogenous
causes, or that real consumers save bandwidth/tokens/time. A PASS is only a
method-scoped construction result, not authority, task-effect, production
safety or universal sufficiency.
