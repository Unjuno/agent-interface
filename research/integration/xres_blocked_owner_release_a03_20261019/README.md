# Blocked owner I/O with independent X11 release A03

**Status:** `LAUNCH_SETUP_FAILURE / PROBE_NOT_INVOKED` (2026-10-19). No trial ran.

A03 is a fresh bounded construction attempt after A02 failed before any accepted trial because its event receiver crashed on a non-key X event. The only code change is to discard events other than KeyPress/KeyRelease before reading `detail`. A02 source, raw, and result remain immutable.

The retained experiment scope requires an independently observed task KeyPress and key-down state while the owner remains blocked in XSync, exact XRes owner-client disappearance before release, independent release delivery, and key-up state after release and a 50 ms settle. Eight trials are requested; any first failure ends the run.

This is Xvfb-only evidence for a responsive X server with the owner reply path blocked. It cannot establish physical input release, behavior under permanent server nonresponse, XWayland, or real application task completion. The recipient event is only a scoped task-effect signal.

A01 and A02 remain separate immutable outcomes. A03 uses its own source, conditions, raw directory, container name and CID.

The first A03 launch exited 1 before the probe was invoked. The PowerShell
argument-array expression split `/repo/research/integration/xres_blocked_owner_release_a03_20261019/probe.py`
into three arguments (`/repo/`, `research/integration/xres_blocked_owner_release_a03_20261019`,
`/probe.py`), so Python treated `/repo/` as the program path and reported that
it could not find `__main__`. This is a launch-construction failure, not an
experiment result. The exact raw log and exit receipt are preserved; the next
attempt uses a separate A04 record and verifies the complete argv before launch.
