# Bounded visual change review after X11 cancellation

This exploratory caller experiment extends #9893. The test captures the pre-action 640x480 X11 window and hashes a fixed HUD crop, then after cancellation/release repeatedly captures the window for up to a 500 ms cooperative decision deadline. The decision uses only the screenshot crop hash: a different hash yields `visual_change_observed`; no observed change by the deadline yields `timeout_unknown`. Both outcomes retain `semantic_effect: unknown`, `task_success: null`, and no review input. A change is a cue to inspect, not evidence of what changed, task success, or permission to replay an action. The experiment does not integrate this review into product recovery.

Four fresh WSLc containers use private Xvfb, Freedoom2 MAP01 ASYNC_SPECTATOR 35 tics/s, skill 1, seed 991031, a 50 ms observed key hold before cancellation, pinned image sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25, one CPU, 1 GiB, and no container network. Order is withhold/cancel/cancel/withhold, with the same script. Engine ammo is independently sampled for evaluation, not used in the review decision. Main at the time is 96b26b653796a74cd20f25ed8ea789481ea69948; runtime Python was matched to 6a9c787d2caf9740612de65bd2539846dd87cad4 in #9891 and intervening commits are research-only.

| Run | Condition | Review | Checks | Review elapsed | Evaluator ammo |
| --- | --- | --- | ---: | ---: | --- |
| t01 | no input | timeout_unknown | 9 | 518.0 ms | 50 → 50 |
| t02 | cancel | visual_change_observed | 3 | 198.1 ms | 50 → 49 |
| t03 | cancel | visual_change_observed | 3 | 192.9 ms | 50 → 49 |
| t04 | no input | timeout_unknown | 9 | 516.5 ms | 50 → 50 |

Both cancelled waits had verified empty key release and unknown partial action effect. The two control reviews correctly returned unknown rather than inferring that no effect occurred. The 500 ms deadline is checked between synchronous captures, so the timeout results overshot it by 16–18 ms; a blocked capture could take longer. These numbers are single-host measurements including capture and PNG encoding, not a hard real-time bound or a baseline speed comparison. The crop is scenario-specific, exact byte comparison is vulnerable to unrelated visual changes, and these same-condition samples do not establish general reliability, semantic correctness, or task completion. The screen and engine observations are not simultaneous.

ZIP files preserve the script, all frames, telemetry and action/cancellation receipts. `python audit.py` independently recomputes frame and crop hashes, deadlines, decisions, release ordering, and control results. No model was called, no action was issued by the visual review, and no product code changed.
