# r90-a01 result

## Frozen outcome

The sole r90 attempt ended `FAIL_OR_UNKNOWN` before input. It was not retried. The public target review succeeded, but the frozen nonblank-surface gate rejected the frame and `experiment.py` refused before sending any input. Recorded values were 660 unique RGB colors and a 0.97625 dominant-color fraction against thresholds of at least 1,500 and below 0.90. `result.json` confirms `input_dispatched=false`, `task_success=null`, and `replay_allowed=false`.

The saved frame is 1280x800 and shows only a title bar over a mostly uniform gray Calc surface; menus, toolbar and grid were not rendered at capture time. The exact frame and native metadata remain in `server-output/19158444952943c196c6fda5220afe4c/calc-review/`.

## Comparison with r89

Both runs used the same pinned image, Calc/Tesseract versions, 2-CPU/4-GiB container limits, 1.0-second post-launch delay, source hashes, task, and nonblank thresholds. R89's reviewed frame had 2,125 unique colors and a 0.66922 dominant fraction and passed. R90's frame failed both thresholds. R90 therefore exposed variable Calc surface readiness under the fixed delay. This is evidence for a bounded observation-only readiness loop before any task input; it is not evidence that the current frame can safely be edited. The guard correctly stopped.

## Cleanup and limits

The owner closed verified with exit code 0 and no input obligations, but the Calc target required SIGTERM cleanup; its clean-exit receipt is unknown/false. No task effect or input release is claimed because no input was dispatched. Docker exit code 1 reflects the preregistered refusal path. The frozen audit has no positive task gates because execution stopped before compiled input; its `FAIL_OR_UNKNOWN` report is retained.

This is one candidate-branch Xvfb Calc run with no provider/model usage. It does not establish task success, effect, release after an action, clean Calc exit, latency improvement, WSLc, MAP01, broad reliability, or project completion.
