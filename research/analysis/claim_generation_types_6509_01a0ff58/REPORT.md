# #6509: caller-generation aliases cross the receipt reader boundary

The unchanged reader accepted caller generation `True` and `1.0` as matching retained receipt generation integer `1`, returning `COMPLETE_VERDICT` in both cases. Its earlier declared contract requires a positive integer generation, excluding bool. Checking only the receipt scalar type leaves this caller-input gap. This is an ordinary isolated API construction result, not an observed production incident.

| Frozen request | Unchanged reader | Positive-int request gate |
|---|---|---|
| int 1 | COMPLETE_VERDICT | COMPLETE_VERDICT |
| int 2 | PARTIAL_UNKNOWN / GENERATION_OR_SCOPE | Same |
| bool True | COMPLETE_VERDICT | PARTIAL_UNKNOWN / REQUEST_GENERATION_TYPE |
| float 1.0 | COMPLETE_VERDICT | PARTIAL_UNKNOWN / REQUEST_GENERATION_TYPE |

One first boundary child ran on native Windows CPython3.12.14 at2026-10-03T06:22:33Z, exit0, using unchanged complete c03 receipt bytes copied from main636986a8. The four requests were frozen at06:21:42Z. All eight calls completed; source/input hashes were unchanged before/after. Raw f51b9a93900daed30258eb0dd02e26ff260560d1cbbd71398199829c368da25d retains full typed inputs and outputs. One separate raw-only audit child exited0, checks all four complete field sets, and rejects5/5 effective copied-data controls: changed legacy outcome, false candidate COMPLETE, erased bool type, deleted row, and changed input hash. Both child PIDs, actual UTC bounds/exits/stdout/stderr hashes and freeze linkage are in results/BOUNDARY.json. Exact absolute invocation paths are retained privately; the public command uses a pinned interpreter hash, actual relative filename and cwd. These timestamps are custody, not latency measurements.

The simple isolated gate checks `type(generation) is int and generation > 0` before delegating to the unchanged reader. For this four-request corpus it refuses the two out-of-contract aliases while retaining the two integer outcomes. Adopt this requirement for future reuse of this archived reader; the current PR preserves evidence only and changes no live reader/runtime. The earlier nine-case process-exit study used integer caller generations, remains unchanged and is not invalidated within that scope. Its writer, 27-child matrix and formal allocations were not rerun.

The reference audit uses a separately written closed four-case table and strict input type checks without importing either evaluated reader. Its five controls were effective JSON changes; this supports only those controls, not universal audit soundness. The generated source/input freeze, first raw, outputs and all first outcomes remain immutable. Captured Windows stdout retains its original CRLF; a new results/.gitattributes rule records that byte-preservation treatment without rewriting frozen files.

Limitations remain: this retained synthetic journal is not proof of truthful semantic verification, live authority or task effects, durability under power loss, concurrent access, arbitrary invalid generations, platform transfer or speed. No GPU/model/container/GUI/input/network experiment or shared configuration change occurred. The small wrapper is a source copy with .py.txt suffix and is not promoted to an executable runtime module. See PLAN.md for prospective H/T/D/C/U, variable meanings, range/types and stop rules.
