# Record launcher failures before condition validation

The retained Calc ep02 launcher reads conditions and checks input hashes before
its try/finally and elapsed timer. Missing conditions therefore cause exit 1
without launcher-result.json. This does not prove a historical attempt was
omitted; it identifies a gap for future all-attempt evaluation in #57.

`launch_recorded.py` wraps an existing Python launcher without changing its
controller, provider or input behavior. It writes and fsyncs an exclusive
attempt-start record before loading that launcher and records returned/raised
outcomes. Reusing the attempt directory is refused before invocation.

```text
python research/integration/integrated_launch_recording_20261113/launch_recorded.py PATH_TO_LAUNCHER NEW_ATTEMPT_DIRECTORY
python -m unittest discover -s research/integration/integrated_launch_recording_20261113 -p "test_*.py"
```

The launcher must still have its required environment and dependencies. The
wrapper runs in-process with the current interpreter and working directory;
it does not sandbox a launcher, extend authority or manage child processes.

`inspect_launch` performs bounded read-only inspection. Missing terminal data
is incomplete, malformed/mismatched records are invalid, and a terminal record
does not establish task success, cleanup or process liveness. Usage remains
unavailable, never guessed zero. No record permits replay. A killed process may
leave a partial record; the inspector does not repair or overwrite it.

Tests connect the exact hash-pinned archived ep02 launcher at commit
`d69368d47f798dc011aa3264f1b0004a0829be04` to the wrapper, exercising missing
conditions and hash mismatch while rejecting any Popen. A separate real child
exits with os._exit(23), leaving its durable start and no terminal. Return,
exception and SystemExit behavior, duplicate attempts, and corrupt records
are also checked. Tests perform no model or GUI input. Git must have the pinned
archive commit available; this is an explicit dependency, not a skipped test.

This outer interval begins on entry to record_launch and ends before terminal
record persistence. It is not total acquisition or verified-completion time.
Planned stages are labels, not execution evidence. Per-stage usage, ownership,
cleanup, schema/preparation costs and a prospectively frozen matched three-arm
cold/warm/invalidation/repair comparison remain open. This change does not
complete #57 or establish an efficiency gain.
