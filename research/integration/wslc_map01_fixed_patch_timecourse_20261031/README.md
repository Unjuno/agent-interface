# WSLc MAP01 fixed-patch time course

This exploratory single-run observation test follows the existing development-selected navigation route in private Xvfb, then compares an 8x8 RGB patch at the center of the 640x480 game window with the same location in later captures. It tests whether that patch difference must increase with elapsed time. The point is fixed geometry, not a model-labeled enemy. There is no model call, subsequent attack, stale-action reissue, semantic target oracle, or matched arm. Game telemetry is evaluation only.

| Allocation | Outcome |
|---|---|
| j01 | Setup failed before game startup: the image's Node entrypoint attempted to load `/python`. Exit 1 and log retained; no game output. |
| j02 | Explicit `/usr/bin/python3` entrypoint; one run, four observations and clean close. |

| Planned wait (s) | Capture-to-capture (s) | Patch RGB mean absolute difference | Game tic |
|---:|---:|---:|---:|
| 0.2 | 0.245 | 0.000 | 188 |
| 0.5 | 0.546 | 35.542 | 198 |
| 1.0 | 1.045 | 4.000 | 216 |
| 2.5 | 2.546 | 2.875 | 268 |

The patch changed and later became more similar to the source in this run. A single late pixel check cannot establish that the pixels stayed unchanged in the intervening period. This does not identify the cause of the change, establish whether a hostile was present, select a safe threshold, compare model latency strategies, or demonstrate MAP01 task completion. The measured points are sequential samples from one trajectory; they are not independent samples and do not establish a rate or reliability estimate. Capture and subsequent input are not atomic.

Both navigation actions completed with verified neutral releases; final owner close also recorded neutral release and the X keymap check found none of W/E/D/A/F down. The game recorded movement during navigation, health delta 0 and kill delta 0; movement is not attributed to a specific key beyond the recorded sequence. Both named containers were confirmed exited and then removed; the WSLc container list was empty afterward.

WSLc used the pinned image `sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25`, network none, one CPU and 1 GiB RAM (host reported no swap limit support), Freedoom2 MAP01 skill 1, seed 991031, ASYNC_SPECTATOR at 35 tics/s. Runner and stop rule were recorded before j01; j02 used the same runner and a corrected entrypoint, with the previous setup failure disclosed before its run. The 153 Python files in runtime/core_v1, runtime/cli_v1 and runtime/guarded_x11_v1 in the read-only source snapshot matched Git main `9f463ad6daf8ad9179d65fc01ebd9a60a26fc1fe` after line-ending normalization; this does not establish identity of every dependency or non-Python file.

The ZIPs preserve runner, conditions, game samples, observation images/receipts, input releases and logs. `python audit.py` (Pillow required, normal Python mode) reconstructs image SHA-256 and pixel differences, validates the two action releases and final empty state, and checks both outcomes. This is a narrow observation result, not proof that faster or parallel model calls improve task performance.
