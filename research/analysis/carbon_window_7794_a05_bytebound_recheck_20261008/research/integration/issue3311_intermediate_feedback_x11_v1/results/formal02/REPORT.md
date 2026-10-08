# Formal allocation 02: PID exhaustion STOP

Task `ISSUE3311-LOCAL-X11-INTERMEDIATE-FEEDBACK-20260928-02`, a successor to
formal-01. The corrected explicit Python entrypoint started the runner, Xvfb,
local server and Chromium process. Chromium startup exhausted the preregistered
64-PID cgroup before the page/window became available. Thread creation failed
in `ThreadingHTTPServer`, and `xdotool` subprocess creation failed with
`EAGAIN`. No Save/Confirm click or model call occurred.

**Disposition: `STOP_PID_LIMIT_PREVENTED_GUI_FIXTURE_START`.** The exception
handler's follow-up request to its own threaded HTTP server also failed, so the
runner could not materialize its ordinary result JSON. Exact failure classes,
exit code, resource profile and absence of saved result are recorded in
`CONTAINER_RESOURCE_STOP.json`. No retry under allocation 02.

Before registering the next allocation, a separate non-GUI capacity check on
the same pinned image at 512 PIDs / 2 GiB successfully created and joined 100
Python threads (`100_THREAD_CAPABILITY_PASS`). This is only environment
construction evidence. Any further GUI attempt must be a new allocation with
the larger bounded resource profile and failure reporting that does not rely
on allocating another server thread.
