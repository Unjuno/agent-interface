# Docker/Xvfb delayed-input recovery integration — R06

## Result

One standard public MCP caller test ran on the pinned Linux/amd64 Docker image
`agent-interface-xvfb-mcp:late-input-r19` (`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`). The
current local worktree runtime was mounted read-only; the container had no
network and a read-only root. The private Xvfb and writable evidence mount
were confined to this container. The unittest and Docker command both exited
0.

The test queued an 8 s delayed XTEST request behind a blocked real Xlib
`Display.sync`, paused that exact private Xvfb for 4,000.350 ms using a retained
pidfd, cancelled through the public MCP caller, and used a test-only 12 s
transaction window. No production timeout or global input policy changed.

| Measure | Result |
|---|---:|
| Public cancel response from cancel start | 309.405 ms |
| Cancel API invocation to return | 255.842 ms |
| Bounded cancellation transaction | 4,014.099 ms |
| Supervisor release readback after cancel start | 4,061.120 ms |
| Delayed-input horizon | 8,502.065 ms |
| Fresh C task input to effect readback | 48.269 ms |
| Final terminal-result query | 10.311 ms |
| Whole unittest | 9.365 s |

The supervisor retired the exact owner and its XRes client, attempted release,
and read A/B up. A separate parent client later read all keys up. The delayed
B press did not appear. However, the old task's exact counted-effect oracle
**failed**: its A effect count increased from 1 to 3, with two post-cancel A
keypresses. The new C task on a distinct window/session passed its exact
single-effect oracle, release checks, and all nine generation/fence checks.

The original call remains `runtime_failed`, `release_confirmed=false`,
`cleanup_status=UNKNOWN`, `task_success=null`, and `replay_allowed=false`.
External release readback and the fresh task do not upgrade that result. Final
teardown observed A/B/C all up.

## Efficiency interpretation

This run reports a recovery latency vector, not a single speed score. The 309 ms
public cancellation response is bounded responsiveness; the 4.061 s release
readback includes the 4 s Xvfb outage; the 8.502 s horizon and 9.365 s test
duration include delayed-effect observation and task/fence checks. The fresh
task's 48.269 ms input-to-readback is a separate task-effect interval.

These numbers are **not directly comparable** with R23's 600 ms one-action
route score (direct X11 = 100, compiled files = 94.99, compiled journal =
100.51). R23 excluded recovery, while R06 deliberately included an outage and
an 8 s delayed-input horizon. R06 therefore makes no claim that the computer
control method is faster than the conventional route. It identifies the old
task's duplicate effects as the remaining correctness blocker despite bounded
recovery observation and a successful new-generation task.

## Integration-spine coverage

Issue #2789 requires one current-main entry path with all six task rows and a
matched direct baseline. R06 covers only part of that boundary:

| Required element | R06 evidence | Status in R06 |
|---|---|---|
| Setup/readiness admission | MCP server creation and guarded observation | Partial; no model/provider setup path |
| Fresh observation and target binding | Fresh Xvfb capture, generation-bound mint and input | Scoped synthetic PASS |
| Guarded input and verified release | Owner retirement, supervisor attempt and separate neutral readback | Physical readback observed; old API remains UNKNOWN |
| Independent effect/result receipt | Exact counted app events and separate property read | Old task FAIL; fresh C task PASS |
| Stale/changed-state refusal | Old UNKNOWN fence preserved after a distinct fresh session | Partial; no independent stale-target mutation/refusal case |
| Bounded recovery and read-only continuation | Bounded release observation followed by a fresh input task | Recovery observed; read-only continuation not tested |
| Six-task accounting and matched direct baseline | Not part of this one-case recovery harness | Missing |

Therefore R06 is not `PASS_INTEGRATION_SPINE_SCOPED` and does not satisfy the
merge-direction gate by itself.

## Custody and limits

Conditions and the pretrial source manifest are in the private task packet
`private-packets/docker_xvfb_delayed_release_recovery_integration_r06/`.
`evidence/result.json` preserves the structured raw report,
`evidence/result.observation.png` the observation image, and the packet also
retains Docker/unittest exit codes, invocation output, Xvfb log/PID and
pre/post-trial SHA-256 manifests. The source snapshot's `mcp_server.py` hash
was checked against the current worktree immediately before launch. A post-run
audit found that the pretrial manifest's runner entry referenced an unused R04
wrapper; the actual inline runner and Docker arguments have been reconstructed
in `RUN_INVOCATION.json` and `CUSTODY_CORRECTION.md`. Treat source identity as
pretrial-verified but runner custody as reconstructed after the run, so R06 is
a scoped diagnostic observation rather than strictly preregistered
confirmatory evidence.

This is one synthetic Xvfb observation. It does not establish native Windows,
WSLc, GZDoom/MAP01, production reliability, queue-drain safety, or a generally
bounded operating-system I/O hang. The prior R04 and R05 setup failures are
preserved as separate local packets; neither sent task input.
