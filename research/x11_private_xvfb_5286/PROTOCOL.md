# Issue #5286: private Xvfb termination construction check

This is a construction-only, CPU-only WSL2 Linux experiment. It must not use
Docker, the GPU, models, network access, fixtures, XTEST, or GUI input.

## Hypothesis and decision

H: a local Xvfb launched in a private user+mount namespace can become ready,
then accept an explicit SIGTERM and exit cleanly without a forced kill. An
independent audit can bind the child mount namespace to the wrapper's recorded
namespace and prove the intended tmpfs mount and unchanged host WSLg socket.

PASS requires every preflight, readiness, namespace, mount, termination,
durability and audit check to pass. Any timeout, unexpected exit, forced kill,
missing evidence, collision, or audit discrepancy is STOP. Run once; do not
retry a failed construction under this issue.

## Frozen run

The runner accepts only a new output directory below this source directory's
`results/`. It writes raw JSON and a complete stdout/stderr log. Xvfb uses
display `:97`, 640x480x24, and `-nolisten tcp`; Python-Xlib makes a local
connection and records dimensions. The wrapper records its host mount namespace
inode; the child records its namespace inode and mountinfo. While Xvfb is alive,
the wrapper independently reads `/proc/<xvfb-pid>/ns/mnt`; the audit requires
that host-side inode to match the child's self-report and differ from the
wrapper's namespace. It checks target plus filesystem type (not mount source,
which Linux may report as `none`).

After successful readiness the wrapper sends SIGTERM to the exact Xvfb PID,
waits for the namespace wrapper to return, records the signal and exit code,
and never retries.
SIGKILL is cleanup only and always yields STOP. The host WSLg socket identity is
captured before and after and must remain identical.

## Commands

First run `python3 -B -m unittest -v test_runner.py`. Then freeze and publish
source hashes and the exact run command to Issue #5286 before the single
construction run. Preserve PASS and STOP records alike. Run `audit.py` once on
the raw output and include its output in the evidence bundle.
