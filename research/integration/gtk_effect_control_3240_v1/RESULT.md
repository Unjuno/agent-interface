# Result — HOLD (not a pass)

Allocation: `issue3240-gtk-app-effect-control-v1`

Frozen base: `fab3b392fb854696312a85a6b859a78369c3e737`
Docker image: `sha256:eb3ce9f5bd0cf358664b9d1ff9bce4cf2ce9f82f72ec700222046fb8fe8b96ba`

The formal allocation ran exactly two fresh Xvfb sessions once, with zero model/provider calls and zero reruns. The independent audit was also run once and its original output is retained verbatim at `evidence/audit-v1.json`. It returned `HOLD_EVIDENCE_OR_EFFECT_BOUNDARY`; do not reinterpret the allocation as a PASS.

## Observations

- The positive GTK arm wrote the exact `{"saved": true, "text": "gtk3240"}` effect and a `save` event. Target XID/PID/title/geometry identity remained stable. Input release was verified empty. The public adapter result is nevertheless `status=partial`, `task_success=null`; this is not adapter task success.
- The raw nested runtime receipt reports `raw_dispatch.status=returned`, `raw_dispatch.result.status=completed`, five completed operations, and a verified empty release. The v1 independent auditor checked `raw_dispatch.result.execution.status`, a field that does not exist; completion is reported at `raw_dispatch.result.status`. Its two `native_execution_not_completed` findings are an auditor schema-path defect, not evidence that native execution failed.
- The render-only arm produced a same-title/same-geometry decoy with a distinct XID/PID and a saved-looking image; the target received no input and has no effect/event file. However, target XWD hashes changed from `f02495cd1421c886770ccae82fa0cfc0d9077c067e22959b07d19e5f16992e70` to `4ecc6335399676c61aa3900431d643d957a13bece72d14978b52f72fae777f77`. Thus the preregistered untouched-pixels invariant failed. Cause is undetermined; repaint/blink/focus effects are hypotheses only.
- Every frozen source hash matched. Formal #2606 acceptance remains false; this was only the preregistered first-rung two-row diagnostic.

## Decision and next step

Preserve this allocation as `HOLD`: the real app effect is observed, but the adapter boundary remains partial, the independent auditor has a schema bug, and the negative-control target pixels were not stable. No rerun or outcome substitution was made. A successor allocation must use a separately frozen auditor that follows the actual receipt schema and a prevalidated negative-control stability criterion (e.g. repeated no-input captures and a preregistered stable-region/state oracle), while keeping app effect, adapter task-success, and visual-render evidence as separate claims. It must be a new issue/allocation; it cannot overwrite these raw results or claim #2606 completion.

All raw files and the original failed audit are under `evidence/`. `FREEZE.json` and the evidence audit manifest bind the frozen sources and raw bundle. Reproduce only as a new allocation; do not overwrite `formal01`.
