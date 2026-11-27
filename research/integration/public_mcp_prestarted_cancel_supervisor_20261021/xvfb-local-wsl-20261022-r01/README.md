# Corrected-source local Ubuntu WSL/Xvfb attempt r01

**Disposition: FAIL before cancellation release.** This is a new local Linux
Xvfb composition of the public MCP caller using the uncommitted parent-owned
PID-source correction. It is not WSLc, Docker, a physical desktop, or an
allocation-backed experiment.

The test reached the real X11 Display.sync() stall after KeyPress(a) and
committed the synthetic application's a effect. The corrected cleanup request
contained owner PID 436 in both owner_pid and owner_generation.child_pid,
so the two earlier missing-field rejections are repaired in this local path.
After the owner process exited with -15, the cancellation supervisor observed
PID 439 at the same X resource base 6291456 and returned
UNKNOWN/stale_owner_identity (resource_base_reused). The test failed at
test_mcp_xvfb_blocked_release_integration.py:684, which expected the XRes
state to be disconnected. The retained report does not independently identify
PID 439's process role; do not infer more from that number.

The public cancellation returned in 43.659 ms and the event-loop heartbeat's
maximum observed gap was 5.800 ms. These timings show response and event-loop
progress for this one schedule, not a release result or a latency distribution.
The post-cancel receipt retained the a input obligation,
owner_release_attempt=UNKNOWN, release_confirmed=false,
task_success=null, replay_allowed=false, and
late_server_request_possible=true. Independent readback after the delayed
request horizon and the task oracle were not reached. The harness's final
teardown later reported both a and b up; that cleanup happened after the
assertion and is not cancellation-release evidence.

## Frozen conditions

- Ubuntu 24.04.3 LTS under WSL2, kernel 6.18.54.1-microsoft-standard-WSL2.
- CPython 3.12.3; Xvfb 2:21.1.12-1ubuntu1.8; x11-xkb-utils 7.7+8build2.
- python-xlib==0.33, Pillow==10.2.0, numpy==1.26.4, mcp==1.30.0;
  all transitive versions are in conditions-environment.txt.
- Private display :88, 1024x768x24, -ac; no developer desktop display.
- Prestarted supervisor enabled, owner-process tracing enabled, cancel-ack
  hold disabled. The fixture queued KeyPress(b) with an 8,000 ms delay after
  KeyPress(a) and blocked the real owner in python-xlib Display.sync().
- Command: bash run-local-xvfb.sh. The script and raw stdout/stderr, report,
  Xvfb log, screenshot, environment, source working-tree diff, and hashes are
  retained in this packet.

The source correction is still an uncommitted working-tree change on top of
commit a5e72673e0b0ae79a9ba88adbb32a8e2b167fa68; git-head.txt records the exact
HEAD, and source-sha256.txt fingerprints the files actually imported. The
test is a single attempt. Its first outcome is preserved; do not rerun the same
conditions and present a later result as this one.

## Next discriminator

Audit why x11_cancel_worker sees another PID at the owner's retired resource
base and currently rejects that state as resource_base_reused. Preserve the
distinction between a known supervisor-owned X client and an unrelated
replacement client; do not turn arbitrary PID mismatch into release authority.
Then add a focused test for the exact owner-disconnect classification and keep
release readback, the 8-second delayed-request horizon, and task success as
separate checks. Any corrected-source Xvfb follow-up is a new attempt with its
own conditions and raw.

## Raw artifacts

prestarted-cancel-xvfb.json is the integrated receipt;
test.stdout.log and test.stderr.log preserve runner output;
prestarted-xvfb.log and prestarted-cancel-xvfb.observation.png preserve the
private server log and observation image. SHA256SUMS binds all packet files
except itself.
