# Stopped-source and completed-branch custody, 2026-10-03

This is an archival maintenance capsule, not an experiment or scientific
application. It preserves two stranded STOP packages as invalid/pre-run records
and anchors six already-preserved source histories before branch-name cleanup.
Neither Issue #5372 nor Issue #5890 is resolved by this archive.

## Separate STOP boundaries

| Preserved subtree | Allocation | Historical execution boundary | Controlling disposition |
| --- | --- | --- | --- |
| `5372_a02_invalid_unaudited/` | `SAFETY-BACKPRESSURE-PRIORITY-FAIRNESS-5372-A02-WSLC-20261003` | Author reports one candidate invocation; one auditor-container launch exited 2 before Python ran; no retry | `STOP_AUDITOR_LAUNCH_PATH_ERROR`; no method PASS/FAIL |
| `5890_intake_prerun_stop/` | `PORTFOLIO-MULTIPLICITY-5890-INTAKE-A01-20261003` | Candidate=0, auditor=0, raw rows=0; no output exists | `STOP_MAIN_ADVANCED_BEFORE_CANDIDATE`; no scientific result |

The #5372 A02 was mistakenly started while the user's selected work was #6749.
Its [author disclosure](https://github.com/Unjuno/agent-interface/issues/5372#issuecomment-5959996030)
and unchanged STOP are not retroactive authorization. The historical statement
that no PR/main change would be made describes that original mistaken task.
This separately authorized maintenance archive does not adopt the experiment,
repair its failed launch, alter #6749, or grant another execution.
Requested 256 MiB and the retained WSLc cgroup/swap warning are not evidence of
effective memory enforcement. Construction passes are not a formal audit.

The #5890 intake allocation is distinct from both the older allocation-01
storage/main-advance STOP and allocation-02's synthetic result. Its own
`STOP.json` names frozen main `b100d9acee4ec99490b2e97066ec6af5312f1ed9`
and observed main `f8e71fc777100281c67a51233b222334fada2863`.
The original source hashes/input hash are retained without change.

## #5372 publication-integrity discrepancies are retained

All FIVE `FREEZE.json.source_sha256` declarations differ from exact committed
bytes: candidate, auditor, fixture, tests and preregistration. The stored
candidate JSON is 39,695 bytes and has actual SHA-256
`13e153262205aa0105f0b3ae29c0233037900c917eb4f8485f8c1d96fe887d85`,
not the historical STOP/Issue claim
`15f00404f9b12ea87726dde5f927a2e068b1325284d519ac1814cb7034ec222f`.
An in-memory diagnostic excluding the terminal CRLF matches the declared raw
hash, but no bytes were removed or written back. This does not establish the
publication mechanism or the exact local source bytes executed.
The stored payload therefore remains invalid, unaudited forensic output; it
must not be treated as a hash-bound original run result or scientific evidence.

[SOURCE_BLOBS.tsv](SOURCE_BLOBS.tsv) is the custody manifest for the exact sixteen
copied Git entries (nine #5372, seven #5890), with original commits/pathnames,
blob IDs, modes, bytes and SHA-256. The unchanged historical declarations are
not a passing custody manifest. [BRANCH_CUSTODY.json](BRANCH_CUSTODY.json) records
the eight source refs and discrepancies. No source/freeze/raw hash was repaired.

## Complete history, without replaying stale indexes

The custody commit has nine parents: its current-main base and all eight exact
source tips listed in `BRANCH_CUSTODY.json`. Both STOP histories and six
completed source histories remain reachable after an ancestry-preserving merge.
The six completed packages (151 original source-path entries) already match
main by exact Git mode/type/blob identity; they are not copied or changed.
Their original result/STOP/transfer limits and added archive qualifications
remain controlling. Historical aggregate-index edits are kept in commit
history, not replayed over current main.

Only this capsule is additive. Existing main files, runtime, workflows,
allocations and scientific classifications remain unchanged. Original CRLF,
trailing whitespace and EOF blank lines are retained byte-for-byte; new custody
documents are whitespace-checked separately. No study module, producer, auditor,
construction test, corruption control, model, GUI, GPU or container is invoked
in this maintenance pass. Syntax/hash observations are not scientific validation.

Do not execute old reproduction commands, replace candidate output, launch the
corrected auditor path, amend either consumed allocation, or infer a scientific
PASS. A successor needs a separate reviewed identity/allocation/window.
Source-ref retirement requires fresh main byte identity, all source histories
reachable, unchanged existing evidence, no open-PR head/base dependencies, and
per-ref expected-tip leases. No active review/application owner is replaced.
