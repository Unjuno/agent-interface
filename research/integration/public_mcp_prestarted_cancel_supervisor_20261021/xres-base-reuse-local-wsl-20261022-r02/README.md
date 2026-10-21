# XRes resource-base reuse diagnostic — harness stopped

**Disposition: `STOP_HARNESS_MISSING_XDPYINFO`.** The isolated mount namespace
successfully provided private `/tmp` and both Xvfb processes initialized. The
runner then failed its readiness check because `xdpyinfo` is not installed in
Ubuntu WSL. It did not connect to either display, start the owner/helper, issue
an XRes request, or send input events. This packet does not contain an XRes
result.

The shared `/tmp/.X11-unix` remained mode `0777`; only the namespace mount was
changed. The first preflight's socket-permission diagnosis was accurate for
the shared namespace; this attempt validates that an isolated tmpfs avoids
that host condition. No packages were installed. A separate r03 replaces the
missing `xdpyinfo` readiness dependency with a python-xlib connection check.

Raw Xvfb logs, runner, conditions, and hashes are retained here. Do not infer
resource-base reuse, release, or task effect from this harness failure.
