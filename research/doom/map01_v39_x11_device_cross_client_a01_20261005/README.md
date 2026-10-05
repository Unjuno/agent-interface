# XTEST device-specific cross-client behavior — A01

This is a frozen, single-run X11 construction experiment for [Issue #59](https://github.com/Unjuno/agent-interface/issues/59). It tests whether `XTestFakeDeviceKeyEvent` changes overlapping same-key semantics when separate X client connections open the same server-provided XTEST virtual keyboard.

The control and device-specific routes each issue W-DOWN from client A, W-DOWN from client B, W-UP from A while B has not yet sent UP, then W-UP from B. A separate X connection samples the core keymap; a focused core Xlib client records matching core key events. The independent auditor reads only the saved candidate raw file.

`PLAN.md` contains H/T/D/C/U. `FREEZE.json` pins the source hashes, main reference, environment, setup and exact decision gate. `inputs/PACKAGE_MANIFEST.json` and `inputs/SHA256SUMS` bind the copied package archives. `ENVIRONMENT.json` records package, OS, library and host facts. `setup/a01`–`a05` preserve the no-input setup attempts; A05 is the successful preflight. `precheck/audit_mutation_precheck.json` records auditor mutation checks before candidate execution.

The Xvfb and xkbcomp packages were extracted into a task-private Linux directory, never installed. Xvfb runs only inside an unprivileged user/mount namespace with a private tmpfs at `/tmp/.X11-unix`; TCP listening is disabled. The shared distro socket directory contained another process's `X0`, which remained outside the private mount and was not modified.

## Frozen run

After verifying the hashes in `FREEZE.json`, the single formal invocation is:

```sh
bash run.sh
```

Run `audit.py` exactly once on `results/a01/raw.json` only if `candidate.py` exits 0. Do not rerun or overwrite the candidate output. Preserve a candidate or infrastructure STOP as the first outcome.

## Scope

This tests one virtual X server and its shared XTEST virtual keyboard. It does not test the Agent Interface runtime, a production GUI or game, physical input, model behavior, useful task feedback, recovery, safety, or MAP01 progress. The X.Org XTEST protocol specification defines core key/button synthesis and warns the extension is not general action journaling/playback; the device-specific library entry point is a separate behavior under test. [XTEST protocol](https://xorg.freedesktop.org/archive/X11R7.7/doc/xextproto/xtest.html) · [XTEST library specification](https://xorg.freedesktop.org/archive/X11R7.7/doc/libXtst/xtestlib.html)

