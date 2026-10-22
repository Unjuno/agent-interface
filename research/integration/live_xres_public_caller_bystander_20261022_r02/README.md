# Public-caller live XRes bystander refusal — R01

Pre-run protocol. This one-shot case uses a private Ubuntu WSL2 Xvfb at `:179`; it is not WSLc or Docker. It starts the real guarded X11 public MCP caller with the opt-in prestarted supervisor, blocks the real owner in the existing delayed-XTEST/`Display.sync()` fixture, then has the supervisor's test wrapper start one distinct bystander process as the first post-retirement X client. The wrapper calls the unchanged `x11_cancel_worker` only when that connection naturally receives the retired owner's exact resource base. The bystander remains connected during the query. The experiment records the public cancellation receipt and an independent keymap readback before the harness neutralizes keys.

The protocol, source identities, environment and no-retry rules are frozen in [`raw/r02/CONDITIONS.json`](raw/r02/CONDITIONS.json). If the bystander does not naturally reuse the base, preserve HOLD and do not invoke the worker or rerun. One permitted trial; no XID manipulation, retries, replacement runs, or global input actions beyond isolated synthetic XTEST keys on the private Xvfb.

This qualifies only the standard caller's live-Xvfb bystander-refusal branch for one sample. It does not establish physical desktop/MAP01 behavior, global input exclusivity, task success, a hard OS bound, matched efficiency/reliability or WSLc portability.

R01 remains preserved as a [preflight-only failure](../live_xres_public_caller_bystander_20261022_r01/DISPOSITION.md): the Xvfb banner hit a Python version-formatting error before the caller or any input was started. R02 corrects that banner and uses a separately frozen display and raw directory.
