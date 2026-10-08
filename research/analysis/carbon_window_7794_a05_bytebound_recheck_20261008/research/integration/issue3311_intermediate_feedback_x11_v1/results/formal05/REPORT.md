# Formal 05 — live X11 intermediate-feedback allocation

## H/T/D/C/U disposition

- **H:** A fresh live Chromium/X11 observation after Save can select Confirm while stale identity/focus is refused.
- **T:** One frozen no-network ARM64 Docker allocation, one runner invocation, zero retries and zero model calls.
- **D:** Raw runner receipt, X11 screenshot, runtime journal, preflight event, independent audit, and this scoped report.
- **C:** Frozen runtime/runner/page/image hashes; server-side fixture oracle; one observation/admission; no user data or external network.
- **U:** GUI/window-manager focus semantics, successful intermediate-state transition, independent effect, model/task economics, and six-task #3311 acceptance remain unresolved.

## Result

**STOP_SAFE_YIELD_STALE_SYMBOL**. Chromium launched in Xvfb and the live EDITING state plus Save target were observed. The first fresh admission returned `stale` because `xdotool getactivewindow` returned an empty string, despite the fixture window being identified as XID 4194307 and titled EDITING. The runtime completed zero transitions and issued zero clicks. The server oracle recorded zero stage events and zero submissions. No Confirm state was reached.

The independently executed frozen 30-gate positive-success auditor returned exit 1 and `FAIL_RAW_AUDIT` (17/30). The 13 failed gates are the absent successful two-transition route/effect, as expected for this safety stop. This is not a positive audit and is not relabeled as a task success. The independent result SHA is `cae34e60b783aa958d3a0b572ace5edc70e5d49f9578b786996dc1c63a55bba2`.

The interface preflight container exited 0 for the pinned image, but the wrapper did not retain stdout; the limitation is preserved in `INTERFACE_PREFLIGHT_EVENT.json`. This allocation was not rerun. The GUI runner and auditor were run exactly once each.

## Reproduction boundary

Pinned image `sha256:dff1c7b56201b4c299883655d98aee3b3f8d7c0c6dd1e4ad6320b942fb5d17fb`, `linux/arm64`, `--network none`, read-only source, 1 CPU, 2 GiB RAM, 512 PIDs. Runtime source SHA256 `93e47e1ab5ae3450bb4acf9ec9d21c9abc44ca93ffaee25683b22039d9a722ca`; runner SHA256 `624d551eeda3d787d5dfb881af19c08cf79e08e439483eb5eac39271b9a7740f`; auditor SHA256 `b8259f7cdf07b5d4af3e33fcf3f51bbc0c4df304f9c1e4bb71650765187ef08c`; page SHA256 `ae253611acb9c2686dbafd471eacbe499d67470c88b0e23aad7a575731caca59`.

Artifacts are immutable predecessor evidence. Any investigation of X11 focus query semantics or WM-less fixture setup must receive a new allocation ID and a preregistered successor; do not repeat formal05. This result does not establish usability, reliability, provider/model benefit, measured efficiency, or completion of Issue #3311.
