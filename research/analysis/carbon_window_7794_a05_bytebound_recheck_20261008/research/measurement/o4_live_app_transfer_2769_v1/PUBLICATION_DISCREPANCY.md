# Publication discrepancy note

The preformal GitHub `PLAN.md` was created manually from the intended H/T/D/C/U text, while local `PLAN.md` was hash-frozen separately and differs in the C paragraph. `FREEZE.json` records the local PLAN SHA-256. The local plan says xterm state changes occur within one window except replacement, but the executed `study.py` actually restarts the xterm process for each state via `_spawn`; the preformal GitHub PLAN wording (“fresh application processes”) is more accurate about the executed mechanism.

Postformal readable `study.py`, `audit.py`, and `controls.py` were initially uploaded with comment-only omissions during manual transfer; branch history preserves those mismatches. They were then corrected to the exact locally executed bytes and verified by Git blob identity. `controls_v2.py` matched on first upload.

These are publication/prose defects, not new experimental allocations. No live session was rerun. The canonical scientific disposition remains **HOLD_FROZEN_CORRUPTION_CONTROL_INCOMPLETE**.
