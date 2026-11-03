# R561: leaked liveness writer negative control

One preregistered, no-GUI/no-input synthetic process experiment on WSL Ubuntu Python 3.12.3, not WSLc. The parent deliberately passed the liveness pipe write end to the supervisor. After the controller killed the parent, supervisor observed no EOF for 250 ms while retaining that write end. After explicitly closing it, the supervisor observed EOF, terminated and reaped its fake child, then exited; the controller independently observed both pidfds become readable and performed no emergency kill. The process returned 0. Timestamps, code, preregistration and output are in raw.zip; script pre-run SHA-256 `1f75e4c44869a05909f28b53fed0139553dba2ecad19c1c29d1033d2a9c9a75e`.

The bounded 250 ms observation is not proof of indefinite behavior, nor does it validate the real owned-session code. It demonstrates a negative control that an eventual production supervisor must avoid: any surviving duplicate of a pipe writer can mask parent death. No input release, WSLc, MAP01, latency or reliability claim follows. Supervisor exit status was not collected independently; the completed child-reap event and pidfd-exit observation are retained separately.

## Additional limitations

Like r560, this fixture uses a directory with `exist_ok=True`, trusts PID files before acquiring pidfds, and identifies events by substring. Reusing its run directory could pick up stale state, and PID identity is not independently bound at pidfd acquisition. The saved log does not establish reuse, but the harness should use fresh exclusive directories and launch-bound structured receipts before further trials. The pidfds showed process exit, not independently collected supervisor exit status.
