# Complete #8094 review scope after current-main integration

## Decision and exact content

Retarget the existing draft #8094 to main after preserving both its own head and dependency #8065. No source rewrite, force-push, main update, or merge approval is implied.

The local integration commit is `238bbb4a8e3ca8e2461cfefaa8c02e89b049b164`, with ordered parents `cc5884ed802260b6236880e3b4ad2ea4abc8a4d8` and pinned main `21fecd58b9de30073c97234124e73b78c67d4b0c`. Its tree `50b4fb7b6870776d82a440a5bde67a737e779ac6` exactly equals the clean prospective merge-tree result. The complete #8065 head `6591b5703862c73d375a6646374ad82a26505bcb` remains an ancestor. #8065 itself is neither modified nor closed.

The old declared-base comparison included 3,179 paths because it compared against the older #8065 branch while this branch also carried main history. Against pinned main, the complete proposed content is 1,341 paths: 1,330 additions and 11 modifications, with no deletions. No canonical goal/method/onboarding docs, CI workflows, configuration, or existing evidence blobs are modified by this delta. This report and its machine-readable inputs are a later additive documentation-only commit; their paths are explicitly outside the 1,341-path pre-report content tree.

## Full partition, with no hidden path exclusions

`full-path-partition.json` lists every path, status, category, and candidate Git blob in that exact content tree. It supersedes use of a selected import closure as a description of the entire PR.

| Category | Paths | Review role |
| --- | ---: | --- |
| Top-level runtime Python | 10 | Controller/Session selection, ordered measured release, observation identity, cleanup and interruption propagation |
| Runtime model prompt | 1 | V39 immediate-action health/ammo validity requirements carried from the dependency |
| Top-level tests | 14 | CLI/backend, identity/frame, typed feedback, renewal/wait, measured batch and cleanup coverage |
| Nested research Python | 12 | Explicitly listed inherited audit, startup probe, frozen candidate and reconstruction code; not claimed inert solely by directory |
| Other evidence/data | 1,304 | Manifests, raw events, images, logs, reports, and inert Python text snapshots |

The main evidence directories are v39_session_loop (577), v15_cleanup_first (342), batch_perkey_measurement (173), v15_perkey_import (112), perkey_owner_guard (39), and the batch-sample-custody results (38). The remaining paths are included in the full partition, including inherited renewal and feedback audits. All eleven modified paths are runtime, prompt, or test files; the remaining evidence is additive.

## Reuse boundary and verification

`closure-comparison.json` checks 81 exact Git blobs: all sources recorded as loaded or hashed by the latest real-child synthetic runs, both non-Python runtime resources, the adjacent test definitions, and every top-level Python change in the full delta. All 81 are identical between the published `cc5884ed...` head and the integration tree. Thus current-main integration introduced no change to that exercised code/resource/test closure. This is source applicability evidence, not a new execution or a claim that unrelated repository state was tested.

The retained cleanup-first 47-method normal/optimized results and full02/full03 positive/full04 negative runs remain results of their original sources and environment. Their applicability to this unchanged closure is retained. Older evidence keeps its own source identity. No formal allocation, game/model, native input, or remote CI was rerun for this metadata/history reconciliation.

Root and existing bugbot reviewed scope; this is technical review only. The branch remains draft until the required independent content agreement, current exact-tree integration check, and actual merge protection/serialization conditions are met. #59 and the full objective remain open.

## Nested research code and collection boundary

The bounded peer check found no checked-in CI discovery path that selects the inherited `candidate_test.py`. Its `unittest.main` is guarded. The tracked broad research unittest command selects `test_*workspace*.py`, while pytest workflow calls select explicit targets. A manual whole-repository pytest run could still collect the `_test.py` file and fail because its historical default sibling controller is absent; the preserved original invocation supplies `V39_CONTROLLER_SOURCE`. No such broad pytest run was performed or claimed passing, and no frozen file was renamed. See `peer-scope.md` for the exact observed boundary.

`runtime-whitespace-tolerant.diff.txt` is a review convenience for the eleven runtime/prompt paths using Git's ignore-space-at-eol option. The full Git tree/blob partition remains authoritative, including original line endings and all tests/data. It does not replace the exact diff for approval.
