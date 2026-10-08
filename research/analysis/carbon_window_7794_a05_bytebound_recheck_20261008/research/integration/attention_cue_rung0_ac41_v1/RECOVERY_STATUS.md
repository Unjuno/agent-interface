# Current publication status — Issue #4316, Rung 0 allocation ac41

This record preserves the exact nine-file hash-bound preformal source set. It
does not claim or reconstruct a formal outcome, and it is distinct from the
metadata-only PR #4322 and any conversation-local Rung-0 pilot.

## Source checks

All nine files listed by the original `FREEZE.json` matched their declared
SHA-256 values on the exact branch head. The seven Python source/test files
passed syntax compilation in Python 3.13.5. The 12 contract tests could not
run: each depends on `construction/b1/c0/case.json`, which is absent from the
branch. The two `BUDGET_SOURCE` payloads are not bound by `FREEZE.json`; one
does not decompress as valid XZ and the other has no identified/verified
format. They are not copied into this source-only record. The original branch
tag retains their exact bytes.

## Formal status and scope

`FREEZE.json` records `formal_batches_before_freeze: 0` for the declared
20-session Rung-0 allocation. No formal session was run in this recovery. The
separate Issue history describes a 28-session local Rung-0 result, but its
508-file source/raw package is not present in this branch or the metadata-only
PR #4322; that report is not attributable to, or evidence for, this ac41
allocation.

Accordingly, this package is **PRE-FORMAL SOURCE ONLY**. It does not establish
human-cue benefit, task-level efficacy, or a completed Rung-0 result. Issue
#4316 remains open; Rung 1 and the global roadmap remain unmeasured/open.
