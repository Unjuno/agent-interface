# R06 — expose the supervisor in the standard caller CLI

The stdio CLI now accepts `--guarded-prestarted-cancel-supervisor` and forwards
it to `create_server`; the option requires `--guarded-owned-process` and remains
off by default. The new CLI test first failed as an unrecognized option, then
passed after the parser/forwarding change. The prerequisite rejection test also
passes before output-directory creation.

The full focused suite ran 107 tests in each mode. Normal mode had one error in
`test_prestarted_supervisor_public_path_releases_once_but_keeps_runtime_unknown`:
the assertion could not find `owner_process_retired` in the returned cancellation
record, then temporary-directory cleanup encountered a Windows sharing
violation on `.cancellation.json.tmp`.
The same test passed alone immediately afterward. Optimized mode passed 107/107.
This mixed result is retained as-is in the raw logs and exit codes.

This is Windows CPython 3.11.9 with deterministic Fake X. It does not validate
live Xlib/Xvfb behavior, release under blocked live platform I/O, late request
exclusion, independent product task success, MAP01, physical desktop control,
efficiency or reliability. No WSLc or Docker allocation was used.



