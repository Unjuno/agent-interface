# MAP01 HUD template review and OCR probe

This exploratory follow-up to #9894 and #9895 asks whether a fixed HUD appearance can distinguish the earlier ammunition cue from the synthetic overlay while preserving uncertainty. First, v01 used retained #9893 and #9895 screenshots to probe Tesseract 5.3.0 with grayscale or red thresholding. The red-threshold probe read the visually labelled 50 as `56`, 49 as `9`, and an overlaid 50 as `5`; grayscale returned empty strings. These OCR settings are not adopted. The screenshots and raw output remain in v01.zip.

A second prototype freezes two exact RGB crop templates from the earlier #9893 s02 frames: manually visible 50 from frame 000 and 49 from frame 003, crop (32,408)-(90,450) at 640x480. It requires a baseline matching the 50 template and reviews new screenshots for up to 500 ms: exact 49 produces `visual_49`, exact 50 continues until `timeout_unknown`, and any other crop produces `unrecognized_unknown`. All outcomes retain semantic effect unknown, task success null, and no review input. The decision uses only pixels; game-engine ammo is separately sampled for evaluation. The audit checks template provenance against the earlier saved s02.zip and verifies every frame and decision.

| Run | Condition | Result | Elapsed | Evaluator ammo |
| --- | --- | --- | ---: | --- |
| v02 | no input | timeout_unknown | 500.7 ms | 50 → 50 |
| v03 | cancel held input | visual_49 | 174.1 ms | 50 → 49 |
| v04 | synthetic overlay, no input | unrecognized_unknown | 59.1 ms | 50 → 50 |
| v05 | cancel held input | visual_49 | 184.1 ms | 50 → 49 |
| v06 | no input | timeout_unknown | 505.0 ms | 50 → 50 |

Cancellation runs observed the held key, interrupted the wait and verified empty release; the original action's effect remains unknown. The overlay is an artificial 8x8 magenta X11 child window, deliberately placed inside the crop. Each run used a fresh private Xvfb WSLc container with Freedoom2 MAP01, ASYNC_SPECTATOR at 35 tics/s, seed 991031, skill 1, image sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25, no network, 1 CPU and 1 GiB. The same script and fixed order were used. Main was 15b94a52745f909905c0a84b91d6b870f5eb142f; mounted runtime matches 6a9c787d2caf9740612de65bd2539846dd87cad4 as recorded in #9891, with intervening research-only commits.

This is a narrow, fixed-resolution exact-match probe using templates chosen from the same game and seed; it cannot recognize other counts, tolerate normal visual variation, prevent a forged matching display, or establish a hit, causal timing, safe replay or general correctness. The cooperative deadline can overrun while capture blocks. It is not integrated production recovery, a model benchmark or a MAP01 completion result. `python audit.py` checks the six archived attempts, frame and template hashes, no-input controls, overlay, action release and result ordering.
