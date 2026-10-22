# Blocked owner I/O with independent X11 release A02

**Status:** `SETUP_FAILURE / NOT_ESTABLISHED` (2026-10-19). No trial passed.

This experiment follows A01's `NOT_ESTABLISHED` result with a separate construction. An independent X11 recipient window records the task-facing KeyPress/KeyRelease. A Unix-socket proxy forwards owner requests to Xvfb but withholds server replies from the owner after setup. The experiment requires the recipient to receive KeyPress and the independent keymap to show down while the owner is still blocked in `XSync`; only then does the parent kill the owner, wait for exact XRes client disappearance, send KeyRelease through a separate connection, and check both the recipient event and keymap readback.

Each trial passes only when all those events occur in that order and the key remains up after a 50 ms settle. A blocked owner whose input was never observed by the recipient does not pass. A timeout, missing event, mismatch, or uncertain release is retained as the first outcome and stops the batch.

This can establish a finite owner-retirement and independent-release result for a responsive Xvfb server when only the owner's reply path is blocked. It does not establish release while the X server itself remains unresponsive, a physical desktop, XWayland, or a real application's task completion. The receiver is a minimal X11 test fixture, and its event receipt is only a scoped task-effect signal.

A01 remains an immutable earlier result in [`xres_client_disconnect_xvfb_a01_20261019`](../xres_client_disconnect_xvfb_a01_20261019/README.md). A02 uses a separate source file, output directory, container name/ID, and fresh WSLc run.

## Preserved first outcome

The A02 WSLc command exited 1 during trial 1 before the parent received a task
KeyPress receipt. The receiver process crashed at `event.detail` while consuming
an X event that was not a KeyPress/KeyRelease (Xlib raised `AttributeError:
detail`). The parent consequently timed out waiting for
`trial-01-press.json`. Because the task-side event recorder had failed, the
required effect-before-retirement gate was not established; no A02 trial result
is accepted and this is not evidence for or against the XRes release mechanism.

The captured files are immutable. [`run-result.json`](run-result.json) records
exit code 1, and [`raw/wslc-run-raw.log.gz`](raw/wslc-run-raw.log.gz) preserves
the exact raw log; its uncompressed SHA-256 is
`51790a9155ad60a42bd551ed197cf2fb5b9c48623bd26bc3f4e55b6abdbab9ad`. The
source SHA-256 was
`21ee3dab4d91f42280f66ecb44a38abd9e201398a7c88fbbaadc4f4646f18e1a`.
The exact A02 container ID was queried after completion and was absent; the
regular running-container list was empty. A corrected receiver is isolated in
A03 and does not overwrite A02.
