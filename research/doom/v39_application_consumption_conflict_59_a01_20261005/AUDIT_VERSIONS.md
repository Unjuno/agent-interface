# Saved-result audit versions

The A01 candidate comparison and `raw/A01.json` are unchanged. The original saved-result audit is version 1 and remains available as `audit_a01_v1.py`, `FREEZE_A01_V1.json`, and `raw/AUDIT_V1.json` with its original stdout and exit receipt. These bytes were recovered from commit `1ced273cc78fde3d0d9e70a147285126bfabecb0`, before the auditor refinement.

The current `audit_a01.py` is the supplemental version 2. It derives strict interval ordering from saved bounds, validates interval shapes, and has mutation tests for altered classifications. Its output remains `raw/AUDIT.json`; it does not replace or reinterpret the A01 experiment outcome. The current `FREEZE.json` pins the supplemental auditor and its tests. No candidate, GUI, game, model, or input run was repeated for this audit refinement.
