# #2558 strict submit-plan gate audit

Date: 2026-09-20 (Asia/Tokyo)

## H/T/D/C/U

- H: the six fresh model plans can be consumed as complete plans only if both field and submit points are independently within the fresh observation frame before action.
- T: audit the six model plans from the OrbStack six-allocation run against the 400x180 source observation bounds, and compare the gate to what the harness actually consumed.
- D: 6/6 field points were in bounds. 0/6 submit points were in bounds: all submit y coordinates were 190 while the observation height was 180. The harness nevertheless emitted action because it consumed only the field point and used a fixed Ctrl+S path; the model submit point was ignored. Prior effect/release results are retained but do not satisfy this stricter gate.
- C: `STOP_COMPLETE_PLAN_NOT_ADMITTED`. The six-allocation result must remain scoped; it cannot be promoted to a complete model-plan execution result. No new action was emitted by this audit.
- U: either capture an observation frame containing the submit control or change the contract/preregistration to explicitly use keyboard submission and remove submit-point authority. Then rerun with a strict pre-action gate.

## OrbStack provenance

This audit analyzes the fresh six-allocation run executed with image digest `sha256:1a16aa431254514de58c909e84e5094a8e894caac11bf4c9d937dde6ea6d6398` under Docker context `orbstack`. It does not alter or replace the prior raw results.

## Evidence

- six-allocation summary SHA256: `95b07b429b95ffff5e175f3d652a8ac251b1004c95615d4fffeba80b9e401901`
- all six field points: in bounds
- all six submit points: out of bounds
- prior harness action path: field point + fixed Ctrl+S; submit point unused
