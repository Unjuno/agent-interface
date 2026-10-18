# V39 feedback-onset custody audit A01

## H/T/D/C/U

**H.** The retained V39 episode cannot establish independently useful task-feedback onset if task scoring is only a post-control aggregate snapshot and action receipts report viewport-pixel change.

**T.** Read-only parse the frozen map01-v39-coast-liveness-live-01 retention manifest, raw runtime/events.jsonl, and report.json. Verify byte length and SHA-256 for the event stream/report, count per-key and scorer/effect event types, and inspect all positive action-receipt scopes. A second PowerShell implementation independently repeats the core checks.

**D.** PASS for this evidence-availability classification if provenance hashes match; the trace has 39 per-key admissions, no per-key release measurement/transition, one aggregate release, one post-control score, no in-run task-effect event, and all positive viewport receipts explicitly say viewport pixels only. Any changed event shape stops for manual review.

**C.** Typed health/ammo observations may be meaningful and drive validity. They do not independently establish that a command produced a useful task effect. A final score establishes episode outcome but not the onset of a kill/progress event. Four visual-change receipts also do not establish game-task value.

**U.** One read-only retained live episode. This does not show that no useful feedback occurred, that a future independently timestamped signal improves control, or how another episode behaves. No model, GUI, game, OS input, container, or live allocation ran.

## Result

Both implementations pass against the original retained allocation:

- Source commit: a3360a86639967b3e4e7f988ccf6a3f9539197cc
- Manifest blob: 35bc3e12ff438576b1f22ef1c2ce5d0a30162f6b
- Event stream SHA-256: 2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381
- Report SHA-256: 719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687
- 634 event rows: 39 input_admission, one aggregate input_released, zero input_release_measurement / input_release_transition, one post_control_score, and zero in-run scored task-effect events.
- Four visible_change effect receipts all explicitly have scope viewport pixels only.
- The sole independent post-control score is 1 kill, 0 deaths, no MAP01 exit. It is emitted after all other runtime event records; it does not timestamp the kill.
- Disposition: NO_INDEPENDENT_USEFUL_FEEDBACK_ONSET_IN_RETAINED_TRACE.

The preserved source is the V39 retention manifest, which pins all 464 retained files (63,880,177 bytes), including the exact event stream and report:
https://github.com/Unjuno/agent-interface/blob/a3360a86639967b3e4e7f988ccf6a3f9539197cc/research/doom/results/map01-v39-coast-liveness-live-01/retention-manifest.json

## Replay

From the repository root, run python3 research/doom/feedback_onset_audit_v1/audit_feedback_onset.py --trace research/doom/results/map01-v39-coast-liveness-live-01; then run the independent verify_feedback_onset.ps1 with PowerShell. Both use only standard library/runtime facilities and leave the source trace unchanged.

## Consequence

Keep the open opt-in per-key instrumentation path separate from task-effect claims. A future matched live run needs per-key admission/up/release records and a scorer-only, independently timestamped task-effect stream correlated to them. Scorer state must remain unavailable to the controller. A viewport delta or end-of-run score cannot recover first useful-feedback latency after the fact.


## Preserved verifier construction stop

The first execution of the saved PowerShell verifier stopped with STOP_EVENT_SHAPE_CHANGED because missing event categories evaluate to null in a PowerShell hashtable. The raw trace was unchanged. The corrected verifier fills absent categories with zero before the frozen gates. The failed verifier execution is retained in CONSTRUCTION_STOP_V1.txt; this was a verifier-construction error, not a change to the audit classification. Both saved runners were then replayed against the exact retained trace.
