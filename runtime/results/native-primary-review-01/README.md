# Primary outcome review in the native desktop path

The six-task runner used to advance after local title feedback without asking
the primary assistant to interpret the outcome. This left the primary semantic
completion boundary unmeasured. `--primary-review` now requires an explicit
task/source-bound outcome (`complete`, `uncertain`, or `failed`) after viewing a
fresh image and the retained operation receipt. Only `complete` advances the
fixed schedule. Missing, malformed or non-complete reviews stop without replay.
This optional mode is shared by the direct and persistent routes; it does not
turn model interpretation into an independent correctness oracle.

## Actual primary use

Source commit `54e719e28`, WSL Ubuntu, system Python 3.12, private Xvfb,
Chrome for Testing, persistent route, seed 991288. The primary assistant in the
conversation viewed both grounding images and all six saved-result images. It
authored each review before the final evaluator was read. No helper model or
subagent was used. The run process exited 0 as observed by the execution tool.

- Six independently recorded submissions, each exactly matching its task token,
  without missing or duplicate tasks.
- Task 4 refused the old layout with zero emissions. One primary grounding repair
  from the new image completed the task.
- Six explicit primary reviews; the next navigation started only after the
  previous review arrived. Eighteen completed programs retained verified empty
  terminal input state.
- All three tracked child processes were terminal, with exit codes 0/1/0.
  This does not establish complete descendant cleanup.
- Local checks: 171 protocol tests and 68 harness tests passed (239 total).

## Timing and limitations

A separate direct-route stop control (`native-primary-review-stop-01`, source
`a8b9cfa17`, seed 991289) deliberately returned `uncertain` after the primary
assistant viewed a successful task-1 Save. The process exited 1, retained the
review and error, and performed no task-2 navigation. The independent evaluator
correctly retained overall failure with one submission and five missing tasks.
Both completed programs had verified empty release and all tracked children
were terminal. Its 30 files are in `stop-control.tar.gz` with a separate manifest;
the successful-run archive is unchanged. This is an injected stopping control,
not naturally occurring model uncertainty or a matched direct baseline.

See `measurements.json` for all six rows. Action-to-feedback was 634.7–722.0 ms
on the five tasks without repair. Task 4 took 24.04 s including primary repair.
Feedback-to-primary-review ranged from 23.59 to 32.49 s, median 23.85 s.
This latter interval includes another screenshot, tool transport, polling,
image/receipt inspection, conversation work and decision publication. It is a
recorded explicit acknowledgement boundary, not the instant of cognition or
pure model inference latency. No human-tempo benefit is established.

This is one construction/use run, not a preregistered comparison. There is no
new matched direct run, independently attested model identity, actual model
token count, cost or overall integration acceptance. The primary review is not
independent scoring: compare it against the separately retained submission
history. The full raw request, decision, timing, images, guards, operation
receipts, cleanup and local test logs are retained in `evidence.tar.gz` (225
files); no archived run is overwritten.

Run `python runtime/results/native-primary-review-01/verify.py` for read-only
hash, task, review ordering, image, release and timing checks without extraction.

Integration scope: closes the missing explicit primary outcome-review boundary
in the native six-task path under #2789. Overall disposition remains
`HOLD_INTEGRATION_INCOMPLETE`. It adds neither a generic queue nor a sensor.
