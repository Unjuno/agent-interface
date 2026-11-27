# A14 non-child owner-death observation successor

A13 is preserved as a supervisor-waitpid STOP: the owner service is a child of the live session, so the supervisor cannot wait on it directly. A14 keeps the same owner-only SIGKILL target and independent two-key/Button1 observation, but verifies process termination by polling `/proc/<pid>/stat` until the service is zombie or absent. It leaves the session alive during the release observation and separately records receipt presence.

One candidate invocation; no retries. The scoped decision is only whether X11 disconnect clears all key/button state and emits releases; no receipt means no verified owner recovery.
