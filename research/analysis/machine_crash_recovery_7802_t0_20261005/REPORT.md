# Issue #7802 T0 result — machine-crash recovery model

## H / T / D / C / U

**H.** In a finite declared persistence model, a machine-crash cut may produce a recovery image absent from the corresponding process-crash control; inconsistent effect/receipt states must remain `UNKNOWN_RECONCILE`, not be inferred from the local receipt. The separate Issue-level host-stack hypothesis is not tested here.

**T.** Allocation `MACHINE-CRASH-7802-T0-20261005-01` used the frozen ten-scenario fixture on `main@21fecd58b9de30073c97234124e73b78c67d4b0c`. A standard-library candidate emitted one row for each process- and machine-crash image. A separately coded raw-only auditor reconstructed expected rows and classifications from the frozen fixture and applied four mutations. Formal candidate and auditor were each invoked exactly once, sequentially, with no retry.

**D. `PASS_METHOD_SCOPED_T0_ONLY`.** Candidate exit 0; 31 rows. The auditor independently reconstructed 31/31 rows with no errors and exit 0. It found three machine-only state tuples not present in the process-crash control set: `(effect confirmed, receipt absent)`, `(effect confirmed, receipt pending)`, and `(effect confirmed, receipt torn/invalid)`. Classification totals were 13 `EFFECT_AND_RECEIPT_CONFIRMED`, 3 `NO_EFFECT_CONFIRMED`, 11 `UNKNOWN_RECONCILE`, and 4 `CORRUPT_OR_UNTRUSTED`. The four frozen audit mutations—classification flip, duplicate row, image mutation, and row omission—were all rejected.

The observed direction is as intended within the authored model: a missing or nonterminal receipt alongside a confirmed effect remains `UNKNOWN_RECONCILE`; a terminal receipt without independently confirmed effect also remains unknown; torn/invalid receipt bytes are untrusted. This demonstrates that the small model distinguishes process-visible cache state from its allowed machine-crash images, not that any real host produces those images.

**C.** The persistence contract and allowed images are hand-authored and finite. A production effect oracle may be unavailable; actual filesystem, controller, VFS, SQLite and application ordering behavior may differ. Same-store atomicity only applies if the effect truly shares that transaction domain.

**U.** Synthetic method/model only. No Agent Interface journal code, real filesystem durability, SQLite, operating-system or power-loss behavior, exactly-once execution, recovery policy, or external effect was tested. Same-author candidate and auditor code is separate implementation, not independent human authorship. This T0 does not satisfy or authorize Issue #7802's conditional VM T1.

## Reproduction and artifacts

See [`FREEZE.json`](FREEZE.json), [`RUN.json`](RUN.json), [`fixture.json`](fixture.json), and [`COMMANDS.txt`](COMMANDS.txt). Raw candidate output, stdout/stderr and auditor output are preserved under [`results/`](results/). Construction tests passed 8/8 before freeze; the deliberate pre-implementation RED runs are development evidence, not formal candidate/auditor invocations.
