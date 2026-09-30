# Issue #5243 — natural Xvfb reset/terminate construction successor

Status: new bounded construction allocation; no formal XTEST input.

## H / T / D / C / U

**H.** Omitting Xvfb's `-noreset` and enabling `-terminate` lets the last
Xlib client disconnect cause a natural X-server reset and clean process exit,
without SIGTERM/SIGKILL or mutation of WSLg's shared socket directory.

**T.** Frozen current main is `c45e1947e498dce08abfb27e459e610054a0602e`.
Arch WSL2, CPython 3.14.5, python-xlib 0.33, util-linux unshare/mount 2.42.1,
Xvfb xorg-server-xvfb 21.1.24-1. Run the standard-library controls and one
fresh private namespace Xvfb `:98` at 640x480x24. The only changed server
policy is `-terminate` with no `-noreset`. No Docker/OrbStack, network, model,
GPU, WSLg display, fixture, XTEST/HID or application input.

**D.** `PASS_PRIVATE_XVFB_RESET_TERMINATION_CONSTRUCTION_ONLY` requires a
distinct child mount namespace; tmpfs exactly at `/tmp/.X11-unix`; successful
Xlib 640x480 query; natural Xvfb exit 0 within 3 seconds after client close
with no signal fallback; durable raw output; unchanged host WSLg mode/inode/
device; and independent raw audit plus six effective corruption controls.
Otherwise preserve STOP; do not retry this allocation. The controls
include cross-record binding of the host mount namespace inode.

**C.** Fixed display and geometry; one client; TCP disabled. Mountinfo source
may be `none` or `tmpfs` because both are kernel representations for tmpfs;
the mount target and filesystem type must match exactly. Controls cover
namespace identity, mount target/type, Xlib readiness, natural server exit,
and host socket identity.

**U.** One Arch WSL2 host/private Xvfb only. No evidence about XKB changes,
fixture task effects, WSLg/Windows GUI input, concurrency, formal allocation,
or product reliability.

## Frozen bundle

`probe.py`, `audit.py`, and `test_probe.py` are committed before the single
probe. Exact source IDs, command, raw records, independent audit, and hashes
are retained under `results/construction-01/`.
