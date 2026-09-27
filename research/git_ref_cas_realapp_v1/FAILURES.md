# Retained setup/harness/time-limit outcomes

- `git-ref-cas-realapp-20260916-a1`: FAILED_SETUP, 0 scored rows. Python-Xlib aborted because the default Xauthority file was absent.
- `...-a2`: FAILED_SETUP, 0 scored rows. Private empty Xauthority fixed connection; Xlib keysym lookup for `.` failed before a scored block.
- `...-a3`: FAILED_HARNESS. Explicit keysyms fixed input. Git correctly rejected an old-OID mismatch with exit 128 and preserved C, but the harness incorrectly required exact exit 1. The partial block is not promoted.
- `...-a4`: INTERRUPTED. 20-repetition GUI allocation exceeded the outer 120 s execution limit; no final `raw.jsonl`, so no partial result is promoted.
- `...-a5`: INTERRUPTED. 10-repetition GUI allocation also exceeded 120 s. The live config reached ordinal 30, but no final scored JSONL was emitted; no partial result is promoted.
- `...-a6`: COMPLETED. Repetitions were frozen at 3 per cell before execution to fit the execution envelope; 18/18 rows completed.

Each successor changed only the identified setup/harness/budget problem. Scientific comparison logic was not tuned to obtain a favorable result.
