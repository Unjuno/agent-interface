# Event lock owner death probes: r540 and r541

Both probes deliberately held CPython's private `Event._cond._lock` in a child.
The released-lock control exited normally and a second process returned from
`Event.set()`. When the holder was killed while holding the lock, the holder
exited with -9 and the setter was still alive with no receipt after the
one-second observation; the harness then killed and joined the setter. This
occurred once each with `fork` (r540) and `spawn` (r541). The raw JSON contains
the Python, kernel and timing fields. A successful harness exit implies its
bounded cleanup checks did not report a live fixture process.

The experiments are a controlled internal-lock fault, not proof that an owner
will naturally be terminated while inside `Event.is_set()`, a measured failure
rate, a hard bound or a test of actual MCP cancellation. They support a concrete
failure mechanism for the Event-based candidate in #10137: using a process-shared
lock on the parent UNKNOWN/retirement path can make that path wait for a dead
lock owner. Other Python implementations, platforms and versions are untested.

Each source and conditions file was fixed before its run. The r540 first launch
failed because the image's default Node entrypoint interpreted `python` as a
script; the probe did not run. The recorded r540 result is its next launch with
`--entrypoint python3`. R541 ran once with its file mounted read-only and
`--entrypoint python3`. Both used the image digest and Docker resource/network
settings in their conditions files. Raw JSON is copied without alteration from
the controller's output capture. The JSON does not itself attest the Docker
image or flags; these are recorded execution conditions, not independently
attested in-container measurements. No physical input or user GUI was used.
