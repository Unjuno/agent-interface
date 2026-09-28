# Queue lease addendum for formal/audit phase

The frozen `FREEZE.json` records the original -04 assignment (queue comment
5861732940). The subsequent lease-return chronology remains preserved in
Issue #5085 comment 5861754374. On 2026-09-28, the user directly confirmed
that the latest queue checkpoint grants the #5133 -04 CPU-only lease and
instructed this task to proceed. The confirmation is recorded as a fresh
queue comment, #5861775163; it does not alter the freeze or construction
receipt.

Authorized remaining boundary: one formal invocation after immediate exact
main/owner/inventory/output/source/image recheck; then, only if formal exits
zero, one separate independent raw-only audit; then release. No retry or
concurrent container. Construction-04 already ran once and passed; do not run
it again. Allocation -03 remains an immutable construction STOP.
