# Current-source compatibility result (#8244)

**PASS_CURRENT_MODULE_COMPATIBILITY**, 2026-10-06. Main adoption remains subject to current-head checks and nonauthor review. This is not a speed measurement, full CLI/MCP/backend/repository PASS or product acceptance.

## First result

The source-frozen worker ran once:96 exact inputs and192 old/proposal calls. Every output pair is byte-identical and every caller input unchanged. Independent decoding reconstructs all96 original views. Output types over both arms:144 v2-event-reference and48 v3-report-reference. Raw-only audit1261 checks/errors=[];8/8 effective copied-evidence mutations rejected, including consistent corruption of BOTH arms. Actual worker/launcher/audit/controls exits0; no timeout, empty worker stderr. No formal retries, replacements, exclusions or postfreeze source changes.

Excluded construction: upstream11 tests passed plus one expected failure(4 encoding calls instead of1); proposal12/12. Tests cover strict JSON rejection, caller-input separation, escaped/array pointers, literal markers, native/guarded round trips and failed-release/unknown-effect preservation. Those release/task fields are synthetic data, not observed native effects.

## H/T/D/C/U

H: the retained empty-index fast path preserves current-module content, order, reference selection and error boundaries. T:96 exact prepublished inputs crossing depths0/2/8, dictionary/list nesting, four event contexts, both report-reference settings and both raw-report equality cases. D:byte parity, independent roundtrip, input nonmutation, complete source/process records,12 targeted units and8 rejecting mutations. C:maintenance cost may outweigh the small historical local saving. U:full repository/CLI/MCP/backend, arbitrary Python objects, other platforms and real host/model/task value remain untested. Same-author separate audit is not independent human review.

## Change and proof

Exactly four lines are added in compact_receipt, after the existing strict subtree JSON encoding: when the event index is empty, return the already deep-copied dictionary. No fixed empty index lookup can match a descendant. Induction on the finite JSON tree shows the old traversal preserves every scalar, list order and dictionary insertion order; returning the copied subtree therefore preserves content/order and all subsequent reference choices. The nonempty-index path is unchanged. Initial strict encoding remains, so the change does not skip invalid-value rejection.

Full proof, variable/unit table and assumptions are retained in frozen PROTOCOL.md inside SOURCE. Domain: ordinary finite acyclic JSON trees with string keys. Custom subclasses, shared-identity/cyclic graphs, concurrent mutation and recursion/resource exhaustion are excluded. Current complete module blob662a3fc596e9aa3de171ab2f3486fac07ac17dd3; proposal blobea2cd400aa8656d33321b6af8a144082b864f9dd. No guarded/native codec or release semantics changed.

## Chronology and complete retention

Intake main a3e6b0c1ab8d6af5c24abb88a451ce41c4ede028. Source commit ce22783a43887a8a0110f6f2e61399e7161a8b84 and exact-readback comment6016112291 precede the sole run. Result comment6016132798 precedes packaging.

SOURCE:14268 bytes/17 files, SHA25607cad740bf29d833bcb57f5f0e602839768466e5a7aac3823ef8fbac580705eb. RESULT:9520 bytes/15 files, SHA2563c56da282050a1d81194f35a16e09943c4066b34ed55e0c8b0e1106f176f898d. Together retain all32 source/input/raw/freeze/construction/execution/audit/control files. RAW.jsonl646294 bytes SHA2560b61fd999cfdafe052f72d2eec5634d4c7b9384ac856340df29dcb5a7ae704a9. FREEZE SHA25692bbb0e0f01bb4da09d15e0e628cf1cb2838c6d27b9ab2ec46ac6bb94527f5e0. Each binary registration returned the expected local Git blob ID. Frozen archive members are authoritative; readable copies are conveniences.

Publication notes inside RESULT preserve a bytes/string exporter mistake and an unreferenced proposal transcription with a duplicated unchanged guard line. Expected identity checks detected both before reference; the tested proposal was published unchanged. No measurement was repeated or scientific disposition changed. These are local delivery incidents under#8244, not new research tasks or repository-wide defects.

## Reproduction and adoption boundary

From this directory: `python -S -B verify.py`, then `python -S -B test_restore.py`. A fresh32-file reconstruction reproduces original AUDIT.json byte-for-byte;4 packaging refusal tests pass. No measured subject runs during verification. Exact temporary mutation copies are reproducible from frozen controls.py and original RAW; hashes and normal rejection reasons remain retained. Use trusted, quiescent publication and temporary-directory parents; this is not a hostile-filesystem sandbox.

From repository root: `python -S -B runtime/cli_v1/test_receipt_empty_index_r7p4.py`. This focused regression loads the complete sibling module directly, not the full CLI package. Hosted checks, full-suite regression and nonauthor review are separate gates; the focused test is not automatically claimed included in existing explicit CI lists.

Supplied private Linux x86_64/CPython3.13.5 standard-library container. No Docker/WSLc/OrbStack image attestation, shared-workstation lane, GPU, GUI/native input, model/provider, installation or experimental network. Closed#4395 and the old e2r6 timing allocation are not rerun. Prior timing is not a new current-source speed/token/task claim. #3544/#57/#59 and global ROADMAP remain open; keep the owned branch while PR/dependencies remain.
