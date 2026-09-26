# Issue #3794 X11 receiver release-audit successor

Successor study to #3784/#3789. It preserves the #3789 formal STOP and corrects only its false KeyRelease lookup-bytes predicate, then tests the current-main X11 text candidate against the same private InputOnly receiver contract.

Read `PREREGISTRATION.md`, `source_manifest.json`, and `ALLOCATION_FREEZE.json` before execution. The formal allocation is deliberately one-shot. Construction STOP/HOLD and PASS evidence, formal receiver logs, audit output and corruption controls are stored separately. No application effect or product-level claim is implied.
