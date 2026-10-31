# Real X11 release and delayed game effect

This WSLc experiment follows PR #9890 with actual X11 input to Freedoom2 MAP01, using an isolated Xvfb display and GuardedSessionOwner / guarded X11 bridge. The game runs ASYNC_SPECTATOR at 35 tics/s; the test uses 85 ms of held `f` (attack) versus a timed no-input control, skill 1, seed 991031. These are development-selected starting conditions, without model calls, adversarial cancellation, aiming, or a task-completion claim. The pinned image is sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25; each run used a fresh WSLc container, no network, one CPU and 1 GiB memory. Runtime Python files in the mounted snapshot matched main 6a9c787d2caf9740612de65bd2539846dd87cad4 after line-ending normalization (305 files); see manifest. Game ammo is evaluation-only, not available to the control policy.

| Run | Condition | Result | First sample after action | Later sample |
| --- | --- | --- | --- | --- |
| q09 | no input | completed | ammo 50 | 50 |
| q10 | attack | verified release | ammo 50, tic 32 | 49, tic 33 |
| q11 | attack | verified release | ammo 49, tic 31 | 49 |
| q12 | no input | completed | ammo 50 | 50 |

For q10 the release receipt timestamp precedes the first sample, whose ammo is still 50; the later sample reports 49. This is direct evidence that, in this run, verified input release and a single immediate game sample did not settle the eventual game effect. q11's first post-release sample already shows 49, so these observations cannot time its consumption relative to release. Sampling itself is not atomic with the game update; timestamps and tic boundaries bound observations, not the precise effect time. Attack executions completed normally, unlike the cancelled action in #9889. No claim is made about enemy hits, task success, or general delay bounds.

All 12 allocations and their raw results are retained. q01–q04 failed before game launch because PYTHONPATH was absent. q05 and q08 launched but the control used an invalid empty keyboard continuation and failed; q06/q07 were valid attack runs, each showing 50 in the first post-release sample and 49 later, but lacked a valid control. The runner was corrected for q09–q12 so the control performs no action and waits 85 ms. Fixed order, small sample, timing differences, and a single seed limit inference. `python audit.py` checks all attempts, receipts, samples and control outcomes.
