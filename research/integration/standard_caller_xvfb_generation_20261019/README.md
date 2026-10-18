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
black; the exact 24×24 mint patch has standard deviation 0.0. The child window
was painted, but the standard observer reads the root drawable and does not
composite child-window pixels. Preserve the exact report at
[`raw/fourth-failed-run-39173880776.json`](raw/fourth-failed-run-39173880776.json)
(SHA-256 `993C3CF21D4361315217A607F79EF9E67E4E2A0E1736974540049840DBDAEE1B`)
and screenshot at
[`raw/fourth-failed-run-39173880776-observation.png`](raw/fourth-failed-run-39173880776-observation.png)
(SHA-256 `63373382CFA36078355BA24FEB69E5E94474E40EC28F26BB01C8BFD7F4ED18E6`,
2,367 bytes). The fixture now paints the same checker pattern on the captured
root surface in screen coordinates. The refusal was correct for its observed
image; this repair changes only fixture rendering, not the guard or frozen
conditions. All four first outcomes remain separate and preserved.

The synthetic property is not a product task or independent game/app success
oracle. This does not qualify native user desktop input, XWayland, a held-input
release under blocked server I/O, MAP01, bounded general recovery, model timing,
or matched economics. It uses no WSLc allocation, Docker, provider or model.
