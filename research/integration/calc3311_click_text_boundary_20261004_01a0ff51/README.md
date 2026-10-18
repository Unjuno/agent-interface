# #3311 A01 click-to-text saved-boundary audit

This is a model-free, saved-data audit of the first Calc allocation in [#3311](https://github.com/Unjuno/agent-interface/issues/3311). It does not replay the consumed A01 allocation and does not identify the cause of its failed task effect.

## Pinned inputs and reproduction

The audit reads public Git objects at main `8c66c43918c7b8ac4b3daf929e07b163ba306d81`. It verifies the three source copies against `PLAN.json`, checks the saved FODS hash against `task1.DONE.json`, parses the saved cells independently with Python's XML library, and compares the captured program/receipt boundary.

From a checkout containing that commit and its retained study path, run:

```sh
python3 research/integration/calc3311_click_text_boundary_20261004_01a0ff51/audit_saved_boundary.py
```

The command is read-only. It does not start Calc, use X11, send input, invoke a model, start a container, or change the frozen source or raw files.

## Result

All three source hashes match the frozen plan. The saved `task1.fods` SHA256 `c1320d1dc274b60a8d9a3164d47baf340ca24b6dec3b784af982265179e544a4` matches the native completion record. Independent parsing yields A2=9, B2=23, C2=207 with `=A2*B2`, and collateral A3=1; the required values were A2=19, B2=23, C2=437, with A3 empty.

The captured program releases the A2 click at operation 3, sends the first character (`1`) at operation 4, and only then starts a fixed 20 ms wait at operation 5. That wait records `update_observed: null`. The 30-operation program completed and independently verified empty key/button release, but its receipt contains no per-key target or timestamp and no selected-cell readback before typing.

This establishes a missing pre-input selection acknowledgement in the captured path and independently reproduces the saved effect mismatch. It does not establish that a click-processing race caused the mismatch, which native key event reached which cell, or that adding a delay would repair it. The appropriate next live diagnostic must observe the target selection before the first character and record input/observation clocks under a fresh, isolated, model-free allocation. No wait/default change is proposed here.


## Independent check of the later D01 diagnostic

`reaudit_d01.py` reads only the D01 Git objects pinned at commit `f89e59c33a5ca18e9b0a917a596a55b9a99467a6`. Its separate XML reader re-scores all eight prime/trial FODS pairs, verifies each file's SHA-256 against that task's `saved_sha256` in `raw.json`, checks the frozen 0/50 ms row schedule against the saved operations, and verifies the recorded no-model and neutral-cleanup receipts. A replacement FODS with plausible cells but a different digest is rejected before scoring. Run it with:

```sh
python3 research/integration/calc3311_click_text_boundary_20261004_01a0ff51/reaudit_d01.py
```

The independent check matches all eight rows: prime 11/13/143 and trial 73/79/5767 with the required product formula and no other populated cells; 0 ms is 4/4 and 50 ms is 4/4. This corroborates the saved effect result only. It does not establish why A01 failed, prove a timing benefit, or qualify a wait default. The D01 producer and allocation were not rerun. The full row-by-row output is in `D01_REAUDIT.json`.

Disposition: `HOLD_CLICKTEXT_CAUSALITY_UNOBSERVED`. The formal A01 first-failure STOP and its remaining censored sessions remain unchanged.
