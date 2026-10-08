# A08 — native Xvfb V13 alias-cleanup successor

**Outcome: `STOP`.** This is a fresh candidate after A07. It corrected A07's output path and focus-scope defect but stopped before owner creation/input submission because the frozen closure omitted `input_owner_v10.py`, required by `input_transition_owner_v3.py`. The first raw is preserved; Xvfb exited 0. No retry occurred.

The A08 audit confirms the Xvfb alias precondition (`a` and `A` both resolve to keycode 38) but no V13 terminal or key input occurred. This is a harness STOP, not cleanup evidence. See `results/A08_RAW.json` and `results/A08_AUDIT.json`.

The candidate uses current-main owner/executor source snapshots and a candidate-only alias guard. No production source changed. No game/model/live MAP01 allocation was used.
