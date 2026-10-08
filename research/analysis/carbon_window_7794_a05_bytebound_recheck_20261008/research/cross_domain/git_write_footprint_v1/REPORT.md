# Read-set validity does not imply state-preserving writes

Decision: RETAIN scoped current-state patch with read/write preconditions and final current-OID CAS. HOLD production promotion. Issue #332.

## Correction to prior interpretation

Read-only reinspection of the exact PR319 raw archive (SHA256 `479011156d40e930fe13d2dc2104ab047f43935370788cd3d4e960fd729c67f7`) verified its 2,047 manifest files. All ten `unrelated_changed` records reset `unrelated.txt` from `u1` before delivery to `u0` after publication, including five of five observed-readset candidates. Every one was labelled `ground_truth_correct=true` by the old oracle.

The historical task was ref replacement with fixed OID B; its original frozen PASS remains untouched and no case was rerun. The overclaim was generalizing that PASS as preservation of unrelated edits. Complete read tracking and current-OID CAS cannot prevent an outdated full snapshot from replacing unrelated current state. A supplemental correction was posted to #315.

## New, explicitly stronger goal

Change only `effect.txt`, preserve all other current entries including absence and current ancestry, and refuse semantic-read conflicts, concurrent edits to the write target, or a target ref changed after validation. This is a task-authored one-file-edit goal, not the old fixed-OID replacement goal.

All policies validate both semantic read paths and use the same Git-native final current-OID CAS. Fixed snapshot publishes B built from the old plan state. Current patch starts with the inspected current tree and changes only effect.txt, with a new commit parented to the inspected current commit. Guarded current patch adds only a mode/type/blob precondition on the write target. These are known concurrency mechanisms, not a novelty claim.

## Frozen results

Publication base `c6d195473be0aa876cc991093262494209c7971f`. Source/plan hashes frozen at `fd2ae619e5e3c769672b14abef1af2a544573f44` before any scored execution. Seven schedules x three policies x three repetitions, 63 fresh bare repositories, one execution per ID. Authored interleavings are deterministic; repeated scenarios are not independent application samples.

| Schedule | Fixed snapshot | Current patch | Guarded current patch |
|---|---:|---:|---:|
| Stable | 3/3 correct | 3/3 correct | 3/3 correct |
| Unrelated file edited | 0/3 | 3/3 | 3/3 |
| Unrelated file added | 0/3 | 3/3 | 3/3 |
| Unrelated file deleted | 0/3 | 3/3 | 3/3 |
| Semantic read changes | 3/3 refusal | 3/3 refusal | 3/3 refusal |
| Write target changes | 0/3 | 0/3 | 3/3 refusal |
| Ref changes after validation | 3/3 refusal | 3/3 refusal | 3/3 refusal |
| **Total** | **9/21** | **18/21** | **21/21** |

Fixed snapshot loses unrelated state in nine cases and overwrites the concurrent write in three. Current patch eliminates all nine non-write losses but still overwrites the concurrent write three times. Adding the write precondition prevents that last loss. The guarded candidate accepts 12 edits and correctly refuses nine, not 21 task executions.

## Conditional mechanism argument

Read validation establishes the authored semantic preconditions in the inspected snapshot. Write validation establishes the authored no-overwrite condition. Constructing the candidate from that snapshot and altering only the authorized path preserves every other mode/type/blob and absence; parenting it to the current commit preserves current ancestry. Successful expected-OID CAS binds the publication point to exactly that inspected ref value. If it changed, publication is refused. Missing read/write dependencies, ABA/history-sensitive rules, or state outside this Git snapshot remain outside this argument.

## Verification

The frozen independent auditor imports no experiment code. It reads full file bytes/modes/types, recomputes blob identities, reads native refs, commit parents and reflogs, and separately checks task correctness and evidence integrity. All 63 integrity audits pass, while task correctness across all controls and candidate is 48/63. No intentional negative control is hidden as a harness error.

15 test methods pass before measurement and again after independent extraction. They include 21 policy/schedule subcases, corrupt objects, omitted read receipts, false write preconditions, changed reasons/return codes, invalid clock types/order, wrong refs/footprints/reflogs, incomplete/duplicate cases, mode-only entry comparison and rerun refusal. All 2,145 new archive manifest entries match. Recomputed full audit and historical review are byte-identical. Scored sources match all four frozen SHA256 values and the four uploaded Git blob identities. Same measured ID reruns: zero. Harness failures: zero. Deliberately wrong task outcomes: 15.

## Conditions and scope

Git2.47.3, CPython3.13.5, Linux6.18.44/glibc2.41, AMD EPYC9V74, CPU affinity0-4, frequency not pinned/shared host, batch1, overlayfs, bare SHA1 repositories. Same-host perf_counter_ns timestamps are checked only for integer type/order; no speed benchmark or calibrated uncertainty interval is claimed. Only generated fixture data. No new Doom, GUI, model or external service calls and no production runtime edits.

H: read validation alone does not constrain an over-broad write. T: prior archive review plus frozen63 cases. D: scoped retention of guarded current patch, with old overclaim corrected. C: intentionally replacing a whole ref or allowing blind writes has a different goal. U: authored dependencies/write scope, one host, three repeats, no automatic discovery, power loss, multi-ref or arbitrary-GUI guarantee. Independent audit still shares the Git executable; it is not verification of Git itself.

Transfer: database read/write conflict validation; current-document patches rather than stale full-document saves; control interfaces distinguishing evidence used to authorize an action from state components it may change. These are design connections, not newly measured application transfers.

## Retention

GitHub contains all four exact executable sources, the source/plan freeze, a losslessly reconstructible plan, per-case verdict CSV, summary and verification metadata. Full raw native repositories, original receipts, full before/after audit trees, historical input archive and the longer report are in the conversation archive ONLY, not uploaded to GitHub/Actions: `git_write_footprint_evidence.tar.xz`, 267456 bytes, SHA256 `b197268e36671a08efad925f93173475a8cd8ef844e3d7f6101b52350ed4ad3e`.

Official implementation references: https://git-scm.com/docs/git-update-ref , https://git-scm.com/docs/git-read-tree , https://git-scm.com/docs/git-update-index . Native conclusions are measured on2.47.3 rather than inferred from newer manuals.
