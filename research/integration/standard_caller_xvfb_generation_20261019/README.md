# Standard MCP caller on private Xvfb — process/window generation and effect

Status: integration harness prepared; no run result is admitted until the
private-Xvfb workflow artifact is inspected and copied here unchanged.

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
window refusal assertions hold. A failing first run remains in raw; repair a
test defect separately and retain the failure. The workflow uploads the exact
JSON report as `standard-mcp-xvfb-generation`; copy that artifact into `raw/`
after inspecting it and record its SHA-256 here.

The synthetic property is not a product task or independent game/app success
oracle. This does not qualify native user desktop input, XWayland, a held-input
release under blocked server I/O, MAP01, bounded general recovery, model timing,
or matched economics. It uses no WSLc allocation, Docker, provider or model.
