# Child-pipe construction A02

A01 remains an immutable `HOLD_CONSTRUCTION`: its candidate runner required a
`python_version` field omitted from its committed freeze and stopped before
child launch. A02 is a separate construction attempt that adds that missing
field, uses a distinct runner/auditor and output directory, and leaves every
A01 artifact unchanged.

The scientific question and transport conditions are unchanged from
`PROTOCOL.md`: exact session `emit` and V39 `reader`/`wait` functions, exact
retained A08 event, real local Python child and stdout pipe, one row, two
per-key release measurements, false authority, empty stderr, exit zero. Only
the runner/freeze wiring is corrected. A02 is frozen before execution in
`FREEZE-A02.json`; its single command is recorded there. No live or formal
allocation is involved.
