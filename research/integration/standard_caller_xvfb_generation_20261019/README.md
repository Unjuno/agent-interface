# Standard MCP caller on private Xvfb — process/window generation and effect

Status: the first private-Xvfb run failed in report metadata collection before
any input was sent. Its unchanged artifact is retained at
[`raw/first-failed-run-39172913554.json`](raw/first-failed-run-39172913554.json)
(SHA-256 `5DF7159E75C1646BD96BC3F9077ADC8C4ED61C698D770063F20180E86C0E7D2F`).
The assertion/run result is preserved as a failure; a test-only metadata field
correction is being rechecked in a separate attempt.

## Question

Does the supported guarded MCP caller carry live XRes/Linux process-incarnation
evidence and direct-window lifecycle evidence from observation through alias
minting and input admission, refuse a destroyed target before another press,
and expose a separately observed effect and release outcome on one bounded
private-Xvfb fixture?

## Frozen conditions

- GitHub Actions `Runtime X11 v1 Integration`, private `Xvfb :88`, 1024×768×24;
  retain the running server's executable path, SHA-256, and installed `xvfb`
  package version in the raw result.
- Create one small patterned X window in the test process and verify XRes's
  `LocalClientPID` equals that process. Recompute the expected
  `xres-linux-process-v1` digest from target XID, PID and `/proc` start ticks.
- Use the public `create_server`/MCP tool path with guarded-X11,
  process-identity, query-worker, window-lifecycle and owned-process modes.
- Observe and mint from the actual returned source, send one lowercase `a`
  through `interface_guarded_input`, and retain MCP release plus independent
  X keymap readback.
- A minimal synthetic target application waits for the actual X KeyPress and
  changes one window property. A second X connection reads the property as
  effect evidence. Capture monotonic times for observation, input, app event,
  effect commit/readback and stale-target refusal.
- Re-observe and mint a second alias, destroy the target window, then try the
  old alias once. Require refusal, retired lifecycle reader and no input
  dispatch. Do not remap, rebind, retry or replay.

## Decision and limits

Pass is scoped to caller composition on this Xvfb server if all identity,
ordinary input, neutral release, independent property readback and destroyed-
window refusal assertions hold. The first run stopped at `display.info.release`
because Python-Xlib exposes the setup field as `release_number`; the captured
raw reports `FAIL`, `AttributeError`, and no synthetic app events. The test now
reads `release_number`; this repair does not alter the frozen conditions or
upgrade the failed first outcome. The second run passed observation and correctly
refused the target because the synthetic checkerboard occupied only a small
region, leaving the selected source patch flat. Its exact raw is retained at
[`raw/second-failed-run-39173331320.json`](raw/second-failed-run-39173331320.json)
(SHA-256 `DA2AE4BEFDF5BC16CC665F9AFE651F9FEFF21A0F1BD9C061F64688F3D8AF9446`).
The fixture now paints a checkerboard across the full window so the selected
24×24 source patch should be textured in captured full-screen coordinates, but
run 39173486305 still refused it as flat. Its raw is retained at
[`raw/third-failed-run-39173486305.json`](raw/third-failed-run-39173486305.json)
(SHA-256 `D3F71AB59D244E0994EC06E37041EDF9BB6ABDE1CE46A1473E6734802EB2D608`).
The fourth run's diagnostic captured the actual full-screen image. It is entirely
black; the exact 24×24 mint patch has standard deviation 0.0. Preserve the exact report at
[`raw/fourth-failed-run-39173880776.json`](raw/fourth-failed-run-39173880776.json)
(SHA-256 `993C3CF21D4361315217A607F79EF9E67E4E2A0E1736974540049840DBDAEE1B`)
and screenshot at
[`raw/fourth-failed-run-39173880776-observation.png`](raw/fourth-failed-run-39173880776-observation.png)
(SHA-256 `63373382CFA36078355BA24FEB69E5E94474E40EC28F26BB01C8BFD7F4ED18E6`,
2,367 bytes). Two subsequent root-draw attempts, before and after child mapping,
also retained the same all-black image. Their exact reports and identical
2,367-byte screenshots are preserved as
[`raw/fifth-failed-run-39174045103.json`](raw/fifth-failed-run-39174045103.json)
(SHA-256 `ADEDFFCEB400CEFA4746ED4B2777AE89562320EF59E16A5286F7545C0E4A8345`),
[`raw/sixth-failed-run-39174145812.json`](raw/sixth-failed-run-39174145812.json)
(SHA-256 `DA48AC99B32597F2861474991909BBC7181B86C37FCBEE8E727ABDC7CC45FA07`),
and the matching screenshots at their paired `-observation.png` paths (SHA-256
`63373382CFA36078355BA24FEB69E5E94474E40EC28F26BB01C8BFD7F4ED18E6`). These
results showed that the root drawing attempts did not texture the observed
screen. The fixture was then changed to paint the mapped child surface directly.

Run 39174301979 passed the scoped assertions through the standard guarded MCP
caller. It used X.Org Xvfb `2:21.1.12-1ubuntu1.8` (`/usr/bin/Xvfb`, binary
SHA-256 `6b27845931670c8c9b3ce7423696a452ce3cab1c7f316ce5f7ea7f1297fa2f84`).
The retained 19,023-byte report is
[`raw/seventh-pass-run-39174301979.json`](raw/seventh-pass-run-39174301979.json)
(SHA-256 `C3046098A202481AB0841D9957D0CC47E26B0F26DF13B08013638C7D176C1236`);
its 2,940-byte observation is
[`raw/seventh-pass-run-39174301979-observation.png`](raw/seventh-pass-run-39174301979-observation.png)
(SHA-256 `751E00D5F926A15128A45BAEC1B2310AABEE740B363119BD79DD224986D81F01`).
The report binds XRes PID and `/proc` start ticks, process/window generations,
standard-caller input, exact KeyPress/KeyRelease delivery, a verified neutral
release receipt, independent property value `[1]`, and independent keymap
readback `keycode_a_down=false`. Destroying the target caused stale input to be
refused with `input_dispatched=false`, the target-query worker retired, and
`review_required=true`; close then verified neutral state. Recorded durations
were 605.0 ms observe, 56.3 ms input through caller return, 0.15 ms independent
effect read, and 40.0 ms stale refusal. These are one synthetic private-Xvfb
run, not latency bounds or an efficiency comparison. All six failed first
outcomes remain separately retained.

The synthetic property is not a product task or independent game/app success
oracle. This does not qualify native user desktop input, XWayland, a held-input
release under blocked server I/O, MAP01, bounded general recovery, model timing,
or matched economics. It uses no WSLc allocation, Docker, provider or model.

## Additive successful rerun — workflow run 39174461630

The later `Runtime X11 v1 Integration` workflow run
[39174461630](https://github.com/Unjuno/agent-interface/actions/runs/39174461630)
also completed successfully. Its `x11-integration` job
[117814163206](https://github.com/Unjuno/agent-interface/actions/runs/39174461630/job/117814163206)
ran at PR head `8ce4e52a28d393128dc769fc35bcaecd22c94a08`; the uploaded
`standard-mcp-xvfb-generation` artifact was ID `12153533548` with GitHub digest
`sha256:df979bbbd99c38b871c4472c2f7d2c4772a1cd0b487c0ea55b4e09e310d8f1b1`.
The extracted 18,972-byte raw report is preserved at
[`raw/eighth-pass-run-39174461630.json`](raw/eighth-pass-run-39174461630.json)
(SHA-256 `ECD805691D82E4E41870A5F933F998EC31047D769F538C5B14F50E866E0E01B9`).
Its observation PNG has the same SHA-256 as the seventh run
(`751E00D5F926A15128A45BAEC1B2310AABEE740B363119BD79DD224986D81F01`), so the
byte-identical retained seventh-run image is referenced rather than duplicated.

The run again reports `PASS_SCOPED_XVFB_STANDARD_CALLER` on X.Org Xvfb
`2:21.1.12-1ubuntu1.8` with the same Xvfb binary SHA, XRes 1.2, embedded
conditions, and unchanged test/runtime source blobs as the seventh pass. The
independent application-property read returned `[1]`; caller release and
independent keymap readback both verified the key was up. Destroyed-target input
was refused with `input_dispatched=false`, and the lifecycle query worker
retired. The fresh monotonic sample recorded 596.965 ms observe, 4.313 ms mint,
59.479 ms input through caller return, 0.280 ms from synthetic KeyPress to
property commit, 0.139 ms for independent effect read, and 4.069 ms stale-target
refusal. The exact report also retains event and operation timestamps.

This is a second successful sample of the same scoped synthetic Xvfb caller
test, not a latency distribution, product task success, blocked-I/O release,
MAP01, or matched efficiency result. The two successful runs' timings must not
be promoted into a bound or pooled with other interfaces. All six earlier
failed attempts and their raw records remain unchanged.

## Descriptive timing comparison of the two successful runs

The exact raw monotonic timestamps give the following per-run durations. Delta
is run 39174461630 minus run 39174301979; event-to-effect is the synthetic
KeyPress timestamp through the target's property commit.

| Stage | Run 39174301979 (ms) | Run 39174461630 (ms) | Delta (ms) |
|---|---:|---:|---:|
| Observation caller round trip | 605.024 | 596.965 | -8.059 |
| Alias mint caller round trip | 4.094 | 4.313 | +0.219 |
| Input caller round trip | 56.268 | 59.479 | +3.211 |
| Synthetic KeyPress to property commit | 0.179 | 0.280 | +0.101 |
| Independent property read | 0.148 | 0.139 | -0.009 |
| Stale-target refusal caller round trip | 3.970 | 4.069 | +0.099 |

These are stage-specific elapsed times from two separate workflow runs, not
model-in-the-loop task latency. Both runs used the same Xvfb version, bytewise
identical frozen conditions and identical caller test/runtime source blobs. The
two-run observed ranges are descriptive only: they do not establish a
population distribution, confidence interval, upper bound, speedup, or
reliability estimate. The six earlier fixture/debug failures remain part of
the execution history and are not combined into a pass-rate estimate for a
stable frozen candidate.
