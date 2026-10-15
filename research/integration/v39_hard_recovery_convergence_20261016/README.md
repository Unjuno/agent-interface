# Saved V39 recovery-during-cancel evidence: PR8792 convergence

Preservation base `8908da5ed28af1273bddbaf9ebe710dcf5307152`; original PR8792
head `e27c0b43625bbe986b8363c448e52abdb20ebc10`. All 31 original files
are retained byte-for-byte with original-path mappings in `ORIGINAL_FILES.json`.
Their original 30-member checksum file matches completely. Python files use
`.py.txt`, preventing old actors or frozen-source unit tests from accidental
execution/discovery. Historical README/raw/failures are unchanged.

## What the saved data actually establishes

The old local fixture represents health100 ->80 causing hard invalidation,
then96 while waiting for cover cancellation. Its completed pending planner
answer remains rejected despite recovery; a later full frame may seed a new
plan. Cancel precedes planner interrupt. None of this is live screen/input.

Fresh saved-only checks execute only the auditors and audit unit tests in a
dedicated shadow tree, with exact Git source bytes from original commit
`743ae74ec5be2472ff27fa06fe13d5ecf8534de5` as hash DATA. No controller import,
original `run_experiment.py` or producer executes. The two audit unit processes
each pass three methods; original unit code launches auditor children without
`-O`, while separate direct audits run under both normal and actual `-O`.

| Saved record | Corrected audit normal / -O | Meaning |
|---|---|---|
| latest `candidate.json` | PASS / PASS,11 checks each | Includes full recovered fresh-source record and rejected final admission |
| `candidate-normal.json` | FAIL / FAIL | Missing `recovered_fresh_source` and `recovery_observation`; fails fresh recovery admission |
| `candidate-optimized.json` | FAIL / FAIL | Same missing fields; does not prove full fresh-source conjunction |

All three raw cases do retain final refusal and no Executor/input authority.
Their final-admission timestamps differ; they are distinct saved records, not
three modes of one exact execution. The historical claim that normal/-O files
both cover the later full recovered-source conjunction is not adopted. Missing
fields are not reconstructed, results not overwritten, and producer not rerun.

The original v1 auditor has a reproduced saved-data false pass: changing either
final status to READY_FOR_ACTION_VALIDITY or input_authority_admitted to true
still prints PASS. V2 rejects both and four more authority/invalidated-policy
contradictions, six total. V1's historical eight-check label and old raw PASS
are retained as history, not a valid final-admission oracle. A separate reader
imports neither auditor nor controller and checks literal raw authority fields,
event order, timestamps, fresh-source presence and these rejection outcomes.

## Current applicability and limits

Both controller and observable signal guard have changed in current base,
including after line-ending normalization. `final/SOURCE_CROSSWALK.json` pins
old/current hashes and archives both versions as inert source. The saved V2
audit correctly FAILS against current source with exactly controller/guard SHA
errors under normal/-O. Historical PASS cannot qualify current behavior.

The initial new collector incorrectly expected the two older files to pass;
it stopped at normal-candidate-normal.json after that saved-data failure.
Its complete check streams/process receipts and source DATA remain in
`initial/`. The corrected collector records those expected FAILs explicitly
in `final/`; this is a readback correction, not a repaired or rerun experiment.

No production behavior changes, GUI, native input, model/provider, WSL/container
or new allocation. Fixture empty release is not physical per-key evidence;
saved values do not prove pixel recognition, useful feedback, live bounded
recovery, progress, ammo effects, task success or matched efficiency. Keep
#59/#57/#17 open. Use the retained property to design the next current-path
qualification, preserving hard invalidation through cancel and fresh planning;
do not reuse its historical live/resource status as present authorization.

This preservation/correction is the continuation for old PR8792, only after
verified integration. Original branch/worktrees remain. No new quorum or
allocation rule is created by archiving historical metadata.
