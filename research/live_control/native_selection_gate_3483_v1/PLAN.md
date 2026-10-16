# Issue #3483 — visible-selection-gated, explicitly saved Inkscape move

Frozen before allocation or task input, 2026-09-20.

## H / T

Hypothesis: after a fresh click-only stage visibly selects the same rectangle, six Right chords plus a 50 ms settle and explicit Ctrl+S will persist the on-screen move to SVG geometry.

Exactly one fresh allocation: seed 991131; source `81051d732b0180d7762bb2fd4eca6fcd57d2a99c`; arm64 image `sha256:edadb620ecb19dfd8dc5b020e4e134b68188e2bf3902e7d15ae50af55e1af46f`; Inkscape; max two action stages; network none; private Xvfb/Openbox; source read-only; retained Docker interactive TTY; container `issue3435-save-selection-991131-20260920`; evidence root `work/obstac-native-selection-3483-20260920/evidence/`.

Stage 1: click [604,389] only against exact source sequence 1, with unchanged 24×14 guard patch [592,382]. Inspect the exact new linked image. Stage 2 is authorized only if that image unambiguously shows the same rectangle selected; otherwise finish without keyboard. Frozen stage-2 tail: six Right chords, `wait_update(timeout_ms=50)`, Ctrl+S, and explicit `finish_after=true`. Keep PTY attached until terminal reply, then obtain read-only status. No retry, replay, action tuning, or same-seed replacement.

## D

- `PASS_SELECTION_GATED_SAVED_MOVE_SCOPED`: visible selection precedes keys; independently parsed SVG x>50.5, y=50, width=40, height=30, no transform, exclusive tolerance 0.1; lineage, verified empty releases, owner/process termination and container exit verify.
- `STOP_SELECTION_NOT_VISUALLY_VERIFIED`: click image lacks unambiguous selection; no keyboard.
- `STOP_PRE_INPUT_CONTROL_CHANNEL` / `STOP_PRE_INPUT_FIXTURE_MISMATCH`: no task input emitted.
- `FAIL_TASK_EFFECT`: selected-object sequence completes but saved SVG misses target.
- `HOLD_AUDIT_INCOMPLETE`: source/action/release/effect/cleanup evidence is missing or contradictory.

## C / U

One private Inkscape fixture only; no broad GUI, cross-app, performance, cost, human-tempo or production claim. Unknown whether explicit settle/save after the visually gated action preserves geometry and whether cleanup can be independently verified.

## Frozen identities

- Interactive driver SHA-256 `69d15ce78295affad1f15ce65f18c8c07bc993fdf87ac427eb3e91ac55c9012a`.
- Pinned source HEAD and immutable image digest are as above; image inspected arm64.
- New evidence directory empty and container name absent before allocation.
