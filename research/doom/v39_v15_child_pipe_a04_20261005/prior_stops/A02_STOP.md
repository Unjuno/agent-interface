# A02 construction STOP

The baseline child again exited before emitting the fake-session ready event. The frozen runner command omitted the selected V15 script path when starting `bootstrap.py`; the bootstrap therefore treated `--out` as the script path. The readiness gate stopped before any delayed command was sent. This is a harness STOP, not a baseline/candidate poller result. Child stderr was not retained by this runner version, so the exception string is unknown. No game, model, GUI, X server, or OS input ran.

A03 repairs the launch vector by passing the selected V15 script path as the bootstrap's first argument, retaining all remaining `session_command()` arguments unchanged. A01/A02 frozen run files remain unchanged.
