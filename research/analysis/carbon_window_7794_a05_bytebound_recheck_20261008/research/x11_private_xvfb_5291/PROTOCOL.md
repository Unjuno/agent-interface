# Issue #5291: Xvfb SIGTERM outcome successor

## H / T

H: Xvfb in a private user+mount namespace exits cleanly after SIGTERM when the
readiness probe completes before READY is reported, and the run can record the
server and wrapper statuses independently.

T: one construction-only Arch WSL2 run, fixed display :97 / 640x480x24,
private tmpfs socket path, `-nolisten tcp`. No Docker, GPU, models, network,
fixtures, XTEST, or GUI input. The shell emits READY only after a Python-Xlib
probe has completed successfully. The parent sends SIGTERM to the exact PID,
waits once, and preserves STOP on any timeout, forced kill, or mismatch. No
retry under this issue.

## D / C / U

D: frozen source and hashes; CPU mutation tests; one runner output; raw log;
host WSLg socket before/after; child namespace self-report cross-bound to
`/proc/<xvfb-pid>/ns/mnt`; target/type mountinfo; explicit signal result; Xvfb
exit status separate from wrapper exit status; one independent audit.

C: this tests local Xvfb construction and signal handling only. It does not
test GUI automation, input delivery, Docker isolation, or GPU workloads.

U: #5286 raw output showed that its outer runner consumed READY before the
child probe command exited. That allowed SIGTERM during `Display.close()`,
made the child readiness loop continue, and prevented the shell wrapper from
reaping Xvfb before the outer timeout. #5286's raw STOP remains unchanged.

## Decision

PASS requires a successful completed readiness probe, verified Xvfb PID,
explicit SIGTERM, Xvfb exit 0 without forced kill, wrapper exit 0, private
namespace/mount checks, unchanged host socket, and independent audit PASS.
Otherwise STOP. Preserve all raw output and do not rerun.
