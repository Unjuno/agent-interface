# Issue #5243 — private Xvfb construction rung

Status: **construction-only plan; no formal XTEST/input allocation**.

## H / T / D / C / U

**H.** In Arch Linux WSL2, a child running in a private user+mount namespace
can mount a private tmpfs over `/tmp/.X11-unix`, start one Xvfb server there,
connect to it, and exit cleanly without changing the host WSLg socket-directory
metadata. Writing the complete record under the checkout on `/mnt/c` makes the
STOP/PASS evidence durable across WSL process lifetimes.

**T.** Frozen main `7863d1d7c51a42169f2fe291e264f48be9d0a041`; Arch WSL2,
CPython 3.14.5, python-xlib 0.33, util-linux `unshare`, installed Xvfb.
Run the standard-library construction tests, then one Xvfb start/ready/connect/
terminate probe in `unshare --user --map-root-user --mount --fork`. No Docker,
OrbStack, GPU, model/provider, network, WSLg display, fixture app or XTEST input.
The output directory is created exclusively and must not pre-exist.

**D.** `PASS_PRIVATE_XVFB_CONSTRUCTION_ONLY` requires the tests and independent
auditor to pass; child and host mount namespace IDs differ; the child mountinfo
shows a tmpfs exactly at `/tmp/.X11-unix`; Xvfb reaches ready and an Xlib client
reads the expected screen; Xvfb exits 0; output persists under the checkout;
and host WSLg socket directory mode/inode/device are unchanged. Otherwise
retain the exact STOP and diagnostics. This does not authorize formal input.

**C.** One Xvfb display number, fixed screen geometry, TCP disabled, no fixture
or input events; all process creation/cleanup is bounded. Five independent
auditor corruption controls cover namespace identity, mount target/type,
readiness, process exit, and host socket identity. Construction tests also
cover output collisions and startup timeout/diagnostic retention.

**U.** One Arch WSL2 host and private Xvfb only. No evidence about XKB remapping,
fixture task effects, XTEST behavior, WSLg input, Windows GUI, concurrent X
clients, formal allocation, or product reliability.

## Frozen implementation

See `probe.py`, `test_probe.py`, and `audit.py`. The exact pre-run commit and
file hashes are recorded in Issue #5243 before invoking the probe. The raw
record and audit output are emitted under `results/construction-01/`.
