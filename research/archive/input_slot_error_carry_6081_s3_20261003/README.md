# Issue #6081 T0 S3 — preserved pre-formal STOP

## Disposition

This package preserves the exact six-file source tree at immutable commit
`c664baf67c8941ed38ec19417c836bbe210feef8` and the contemporaneous Issue #6081
STOP record. The allocation `INTENT-SLOT-6081-T0S3-20261001-01` remains
**STOP / NOT_EVALUATED**. Candidate execution: 0; auditor execution: 0; no
scientific result is inferred or manufactured. No source, candidate, auditor,
or construction test was executed during this rescue.

The Issue STOP comment said `PROTOCOL.md` was absent from the committed tree.
Read-only inspection of the immutable commit now shows that path is present,
and its SHA-256 equals the pre-run allocation's declared protocol hash. This
later Git-tree observation does not establish what the historical runner
working directory contained or invalidate the recorded STOP. Both statements
are preserved as distinct evidence; the historical comment and source commit
are not rewritten, reconciled by assumption, or used to authorize a rerun.

The committed `FREEZE.json` still has `source_commit` set to
`PENDING_THIS_COMMIT_SHA`. It records an unresponsive Docker engine and no
shared container lease. Thus the package does not claim that all allocation
preconditions were met, that a formal attempt occurred, or that construction
PASS establishes scientific validity.

## Exact-byte manifest

`MANIFEST.json` maps every original path to its immutable Git blob, byte size,
and SHA-256. All six paths were additions in the source commit; no prior file
was modified. `VERIFICATION.json` contains the independently recomputed
identities and the protocol hash comparison. Verification is static only.

The allocation-specific archive path keeps this packet separate from S1/S2
(`#6754`) and from the later S4-S7 successor result (`#6357`). Those distinct
allocations, outcomes, and STOP records are not combined, rescored, or replaced.
The original branch remains available until this preservation PR is reviewed;
no branch deletion or tag movement is part of this change.

## Scope boundary

This is preservation of source and a pre-formal STOP, not a method PASS, live
actuator result, GUI/game result, or authorization to execute the allocation.
Any further experiment requires a distinct successor allocation, current
ownership/base checks, corrected independent baseline definition, and its own
immutable path and formal budget.
