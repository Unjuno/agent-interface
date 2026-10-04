# Absolute-window typed-state audit A03

Frozen base: d12d451ae5e7661adc3b261403196b1af72e2851 (recorded in FREEZE.json).

## H/T/D/C/U

- **H:** Although the retained scorer sample schema omits health and ammunition, the raw runtime event stream may contain typed HUD observations during the same six frozen 600 ms windows.
- **T:** Read-only audit of the six frozen `RESULT.json` window bounds and `runtime/events.jsonl` streams. Reconcile every in-window `doom-typed-observation-v1` health/ammo row with its same-run observation metadata key (id, step, sequence, capture timestamp, RGB hash) and saved image path. Inputs and auditor are SHA-pinned in `FREEZE.json`.
- **D:** A03 passes only if all six exact windows are valid, every in-window typed health/ammo value has the expected type/identity/binding, every row joins uniquely to an observation record and existing saved image, and no input hash changes.
- **C:** All six windows contain 27 typed observations total (4 or 5 per cell); all 27 join uniquely to observation records and existing screenshot paths. Every observed health value is 97 and every ammo value is 48. There are zero health or ammo transitions in-window.
- **U:** This adds sampled typed safety-state coverage that was absent from A02's scorer-only analysis. It does not show independently useful task progress: no health/ammo change, kill, completion, or map exit was observed in these short windows. It does not re-extract pixels, attribute causality, establish a treatment effect, or close the live #59 gate.

## Relationship to A02

A02 remains valid about the scorer schema: `scorer-samples.jsonl` has no health or ammo fields. A03 separately audits `typed_observation` events in the runtime log. The distinction matters because typed health/ammo were present, but static values in a window cannot establish feedback onset or useful control.
