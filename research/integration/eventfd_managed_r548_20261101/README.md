# Managed eventfd close prototype r548

One isolated Linux run executed six fixed-order cases. The ordinary signal,
managed close and number reuse, injected failure before close, injected failure
after close plus number reuse, and parent close after transfer to a spawned
child all passed. In the last of these, the child could still observe its own
previously signalled descriptor after parent close. An intentionally unmanaged
external close plus `dup2` of an empty pipe was not detected and the sixth
regression failed; the suite exited 1. Failures before and after close both
remain `UNKNOWN`, and a managed retry does not close a reused integer.

This is a process-local prototype, not wired into owned-session lifecycle. Its
lock cannot protect against arbitrary external `os.close`/`dup2`, cannot revoke
an already transferred child fd, and can itself wait if a thread stalls while
holding it. Descriptor transfer races, startup failure, child death, cleanup
errors, real cancellation, X input and queued requests remain unverified. The
close-error injections do not prove an actual OS error or physical key release.
The prototype and red regression must not be treated as production-ready.

`raw.zip` SHA-256
`a50d344cfda241d317961281995f7e3ca76ba707d00c0ab6f67e0f56097d96e7`
contains conditions, base, pre-run diff, source status, unittest output and exit.
All ZIP members passed integrity checking. The image digest and flags are
recorded conditions rather than independently attested by the unittest output.
