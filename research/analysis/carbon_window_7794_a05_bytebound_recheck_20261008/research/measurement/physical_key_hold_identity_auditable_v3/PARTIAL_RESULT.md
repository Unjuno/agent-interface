# #1043 first outcome — stopped after chunk 04

Disposition: **`STOPPED_COUNTER_SCOPE_BUG`**. This allocation is not continued or reclassified as PASS.

Fixed controls passed 11/11. Five immutable primary chunks completed once (50,000 lifetimes, 525,576 event steps, reruns0) before the frozen auxiliary counter `unconfirmed_fabrication` became nonzero. Candidate/oracle mismatches, false mint, retired reuse, cross-lineage retirement, multi-ID-per-hold, repeated-down instability and active/retired overlap are all zero in those chunks.

The first witness is lifetime18/event16: a known active hold `ownerB:g1:F8` receives an **unconfirmed repeated down** with matching owner/intent. Exact #1023 science returns `ACTIVE_REUSED` with the existing ID and leaves state unchanged. This is explicitly allowed by the scientific H: unconfirmed/preexisting DOWN must not **fabricate a new ID**; it need not hide an already-known active generation. The frozen auxiliary counter incorrectly defined any non-None ID on an unconfirmed event as fabrication.

Therefore the remaining 20 chunks were not executed. A fresh successor may keep exact model/oracle science and change only this auxiliary invariant definition to count fabrication only when unconfirmed evidence creates/changes lineage rather than re-reporting a pre-existing active ID.

No X11/model/task input/shared runtime action occurred.
