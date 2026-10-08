# Construction 01 — STOP

Frozen source commit: `46c9f68eae25f3710a566c887aeffa5f2259f2ba`.
Runner decision: STOP; independent audit decision: STOP.

Passed observations: WSL2 Arch had the required binaries and Python-Xlib;
Xvfb answered a 640x480 local readiness query inside the private mount
namespace; `/tmp/.X11-unix` was a tmpfs mount; the child namespace inode matched
the host `/proc/<pid>/ns/mnt` view and differed from the wrapper namespace; the
host WSLg socket identity was unchanged.

Failed observation: after the runner sent SIGTERM to the recorded Xvfb PID, the
namespace wrapper did not return within five seconds. Cleanup sent SIGKILL to
the process group; the wrapper was observed as exit `-9`. Therefore a clean
Xvfb exit was not demonstrated. The frozen runner conflates the wrapper wait
status with the Xvfb exit status, so the raw `-9` must be interpreted as the
wrapper's forced-kill status, not as a separately measured Xvfb status.

The readiness probe printed `READY=640x480`, then Python-Xlib raised while
closing that connection. Because the child shell treated the probe as failed,
it continued its readiness loop and produced repeated connection-refused
tracebacks after Xvfb stopped accepting connections. This is a runner defect
for a successor: terminate the probe process without an error-prone close,
stop polling immediately on readiness, and separately record the Xvfb and
wrapper wait statuses. This STOP is immutable; do not retry under Issue #5286.

See `raw.json`, `runner.log`, and `audit.json` for the retained evidence.
