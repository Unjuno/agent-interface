# R03 result — FAIL_OCR_EFFECT_GATE

## Disposition

**FAIL_OCR_EFFECT_GATE; no task success.** The normal-mode run launched Edge,
minted both aliases from real Edge screenshots through the exact V5 point-mint
method and real `TargetHandleStore`, and passed caller reuse and final target
revalidation. The compiled path admitted the Field action and CDP inserted the
task token. Its subsequent screenshot visibly contains the exact
`t991025-4`, but the frozen Windows OCR region returned `t991025 S ave` and
the page OCR returned `VaIUe t991025-`. The exact-token predicate therefore
remained false. The compiled runtime stopped with `effect_failed` after one
completed action; Submit did not run, the server recorded no POST, and the
outer task scorer did not run. The exact-value gate behaved conservatively.

The negative changed-generation case and the optimized-mode run were not
started after the first case failed. R03 is not a positive integration result,
not an OCR qualification, and not a model-efficiency comparison.

## Raw evidence and diagnosis

- Frozen conditions/source hashes: [`raw/normal/conditions.json`](raw/normal/conditions.json).
- Runner output and exit 1: [`raw/normal.stdout.txt`](raw/normal.stdout.txt), [`raw/normal.exit.txt`](raw/normal.exit.txt).
- Actual browser frame sequence and task/caller/core receipts: [`raw/normal/positive/`](raw/normal/positive/).
- The screenshot shows the full typed value, while online OCR missed its final `-4` characters. A post-hoc OCR diagnostic on that retained screenshot tried three tighter/larger crops; none returned the exact token. It used no browser or input. See [`diagnose_saved_frame_ocr.py`](diagnose_saved_frame_ocr.py), [`raw/ocr_roi_diagnostic.json`](raw/ocr_roi_diagnostic.json), and the retained diagnostic wrapper/import outputs in `raw/`.
- Initial profile cleanup remained locked after the test's 16 retries. The R03-owned Edge processes were then selected by their exact generated profile marker, stopped, and verified absent; the test-created profile was removed. This cleanup did not change the failed task verdict. See [`raw/cleanup-audit.json`](raw/cleanup-audit.json).

## Scope

This used headless Edge CDP mouse/text dispatch, not OS keyboard/mouse input.
The recorded release is a CDP adapter receipt, not physical-input release.
There were zero model/provider calls and one dispatched action. It establishes
that the composed path can reach real pixels, mint/revalidate aliases, and
stop before the next action when its exact OCR effect gate is unsatisfied. It
does not establish full-path success, generation-change refusal, task
reliability, or efficiency.

## Next finite step

R04 may keep the exact-token acceptance criterion and the external POST scorer,
while making the local fixture's text larger and isolating the OCR region from
the adjacent Submit label. R04 must be frozen separately; R03 remains a
retained failure, and no R03 case is to be retried.
