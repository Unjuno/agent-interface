# Held-key Xvfb disconnect-order discriminator

**Scoped result: `PASS_SCOPED_XVFB_HELD_KEY_ORDER`.** Under the private GitHub Actions X.Org Xvfb (`xvfb=2:21.1.12-1ubuntu1.8`, executable SHA-256 `6b27845931670c8c9b3ce7423696a452ce3cab1c7f316ce5f7ea7f1297fa2f84`), an owner pressed `a`, queued an 8-second delayed XTEST `KeyPress(b)`, and blocked in `sync`. After PID-qualified XRes reported that owner disconnected, an independent X client still read `a` down and `b` up. A separate client released `a` and read both keys up. At 8.5 seconds after owner termination, both keys remained up and the delayed `b` press was not observed.

This narrows the late-request question for this exact Xvfb build, request sequence, and observation horizon. It does not prove the standard MCP caller releases input under blocked I/O, physical key-up on a user's desktop, task effect, MAP01 progress, or behavior on other X servers.

## Frozen conditions and result

The original R01 conditions are in [`conditions.json`](conditions.json); the revised R02 conditions are in [`conditions-r02.json`](conditions-r02.json). The test was added to the existing private-display-only XRes integration module and its raw receipt is required by the X11 workflow. The owner, disconnect supervisor, cleanup client, and independent readbacks are separately identified in the JSON result.

The test code and frozen R02 conditions were merged by [PR #9168](https://github.com/Unjuno/agent-interface/pull/9168) at `fc7d605c4bdab55dfb42ea66bec821f55f012c60`. Run [39221822908](https://github.com/Unjuno/agent-interface/actions/runs/39221822908), job `117958657868`, ran the revised live test on PR #9168 head `277b858db12ea223ae0c43f6bc429de91549d92d`. The job passed and the log shows the named test passed in the private-Xvfb integration step. Its raw is [`x11-held-key-disconnect-queue-run-39221822908.json`](raw/x11-held-key-disconnect-queue-run-39221822908.json).

The observed sequence was:

1. Before termination, the independent keymap read showed `a=true`, `b=false`.
2. The owner PID `2553` was reported disconnected after 60.919 ms; the XRes worker retired successfully.
3. **Before sending any independent KeyRelease**, the separate observer still read `a=true`, `b=false`.
4. The cleanup connection sent `KeyRelease(a)` and independently read `a=false`, `b=false`; `independent_release_effect_observed=true`.
5. At 8,500.314 ms after owner termination, the keymap still read `a=false`, `b=false`; no delayed `KeyPress(b)` was observed.
6. Final cleanup read both keys up.

The server reported vendor `The X.Org Foundation`, release number `12101011`, XRes `1.2`, and XTEST `2.2`. The Xvfb executable hash and package result are retained in raw. The `xserver-xorg-core` package query returned an empty version after the equals sign; do not infer that package version from the `xvfb` package version.

## Preliminary R01 runs and correction

The two earlier receipts, [39221315372](https://github.com/Unjuno/agent-interface/actions/runs/39221315372) and [39221534890](https://github.com/Unjuno/agent-interface/actions/runs/39221534890), are retained as [`run 39221315372`](raw/x11-held-key-disconnect-queue-run-39221315372.json) and [`run 39221534890`](raw/x11-held-key-disconnect-queue-run-39221534890.json). Both observed no delayed `b` through the horizon. They omitted the keymap read after disconnect and before KeyRelease, so their apparent `a` release cannot be attributed to the independent cleanup client. Treat them as preliminary late-`b` observations only; do not pool them as independent release-transition evidence. The R02 condition file records this correction.

## Limits and next boundary

This is one R02 live run on one private Xvfb build with two keys and one XTEST delay. It is not a reliability estimate or a general X-server guarantee. The test uses a direct XTEST owner, not the standard MCP caller; it does not block the caller's platform I/O, observe an application task, or measure task completion. The XRes disconnect observation is separate from any claim about physical input or application success.

The next decisive integration is the same queued-request ordering through the standard caller and a real X server while its owned input path is synchronously blocked, with caller-visible bounded recovery and independent application/task evidence. WSLc remains unavailable until its current owner and unused allocation are verified; these runs used only the workflow-owned private Xvfb.

The machine-readable check is [`audit_raw.py`](audit_raw.py). Conditions, raw receipts, test source identity, and workflow identity are bound by [`SHA256SUMS`](SHA256SUMS).
