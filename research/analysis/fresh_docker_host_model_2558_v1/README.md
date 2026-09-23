# Fresh Docker → host model result (#2558)

The fresh Docker allocation created a valid X11 observation and verified
release, then stopped before input because the native assistant-request path
timed out. The generated observation was independently sent through the new
host-local model bridge and returned a schema-valid compiled grounding plan.

This is deliberately recorded as a stopped run: the host bridge result does
not retroactively authorize the timed-out native program and no task success
is claimed.
