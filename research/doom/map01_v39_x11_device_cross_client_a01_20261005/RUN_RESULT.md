# A01 result — device-specific XTEST does not isolate client holds

**Disposition: `FAIL_CROSS_CLIENT_ISOLATION` for the frozen hypothesis; candidate and independent audit completed successfully.** The core `XTestFakeKeyEvent` control and the device-specific `XTestFakeDeviceKeyEvent` route had the same observable result on Xvfb: A-DOWN made the keymap down and delivered one focused-client KeyPress; B-DOWN left the keymap down and delivered no second KeyPress; A-UP made the keymap neutral and delivered KeyRelease while B had not sent UP; B-UP made no further core event. Both connections opened the same server device, `Virtual core XTEST keyboard` (id 5).

The one frozen candidate invocation exited 0. The raw-only auditor ran once, exited 0, and passed 30/30 checks. The retained raw file SHA-256 is `7e98e0e8766d0d3ebf85c03b2965236d098799e1740fa1b43426950dde0a0a8e`; the candidate's stdout hash, WSL source hash, and Windows-side copy hash agree. See `raw.json`, `AUDIT.json`, and `TRANSFER_CHECK.json`.

This observation means the legacy device-specific XTEST call, when both X clients open the same server-provided virtual XTEST keyboard, does not preserve an overlapping client hold from the other caller. It supports the cross-client interference concern for this shared-device route. It does **not** test independently created virtual keyboard devices, Agent Interface's full runtime, a production GUI/game, physical input, model behavior, useful feedback, recovery, or task success.

## Execution and custody

- Setup A05 passed without input: Xvfb opened on `:87` inside an unprivileged user/mount namespace; no packages were installed; no Docker engine or GPU was used; TCP listening was disabled; the namespace's socket directory was a private tmpfs. After teardown the shared `/tmp/.X11-unix` remained mode 777 and contained only the pre-existing `X0` entry.
- The frozen `run.sh` invoked the candidate once, and the inner runner recorded exit 0. The outer shell then returned 1 because it attempted to copy results into a Windows output directory it had not created. That copy failure occurred after candidate completion. I created the destination and copied the retained WSL raw bytes unchanged; `TRANSFER_CHECK.json` verifies their SHA-256. The candidate was not rerun.
- The frozen auditor was invoked once after confirming candidate exit 0 and raw byte identity. No candidate or auditor retry occurred.

Exact inputs, package hashes, setup attempts, frozen source identities, and reproduction commands are retained beside this report. The XTEST protocol specification defines the standard request as core key/button synthesis; this empirical run characterizes the separate legacy device-specific library entry point on one current Xvfb build. [XTEST protocol](https://xorg.freedesktop.org/archive/X11R7.7/doc/xextproto/xtest.html) · [XTEST library specification](https://xorg.freedesktop.org/archive/X11R7.7/doc/libXtst/xtestlib.html)
