# Issue #59 T3 — Xvfb keymap witness construction

This additive successor moves the T2 occurrence-witness prototype from an
in-process fake Xlib transport to an actual private Xvfb server. The test uses
XTEST-generated events only. See [PLAN.md](PLAN.md), `FREEZE.json`,
`CONSTRUCTION.json`, and the one-shot raw/audit under `results/t3-01/`.

The private X server is launched inside an unprivileged WSL user+mount
namespace with a private tmpfs `/tmp`, private Unix socket directory, and TCP
disabled. This avoids modifying the shared X socket directory or contacting
any existing display. Docker Desktop's `desktop-linux` Engine was unavailable;
no Docker service or container is started.

This is only server-side virtual-keymap construction evidence. It establishes
no physical keyboard state, real application effect, input authority, held
duration, live MAP01 outcome, latency, safety, or product benefit. The full
Issue #59 threat-exposure and matched-control gates remain open.
