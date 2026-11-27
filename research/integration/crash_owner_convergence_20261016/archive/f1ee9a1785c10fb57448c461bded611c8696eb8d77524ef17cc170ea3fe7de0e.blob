# V39/V15 process-owner integration contract — A01

**Disposition: `PASS_STATIC_INTEGRATION_CONTRACT`.** The V15 session and V39
controller now have an explicit `--measurement-owner-process` opt-in. The
default session selection remains V12, and the existing V15 telemetry path
remains selected unless process ownership is explicitly requested. The opt-in
backend closes the unused in-process owner, starts the framed process owner on
the session's X display, and emits a ready record with owner, service PID,
display, and receipt path.

Outer control now requires the matching fsynced, verified empty release receipt
and observed service exit both after normal opt-in session completion and in
the opt-in failure-cleanup report. A missing, malformed, mismatched, or
unverified receipt keeps `display_reuse_allowed` false. Receipt validation
accepts verified cancellation releases followed by a final verified close.
V15 source manifests include the added adapter and process backend only for the
opt-in path.

The fixed command in `RUN.json` ran **55 tests successfully** (2 existing
environment-dependent skips), with Python compilation and `git diff --check`
also passing. `audit.py` independently recomputes the frozen source hashes and
checks the preserved test output; `AUDIT.json` reports no errors. The source
hashes are in `FREEZE.json`.

This is a source-composition and unit-contract result only. No full V15 session,
live Xvfb owner recovery through the new backend, game, model, or physical input
was run. In particular, A01 does not establish that the end-to-end session
actually carries a held key through this backend and that the outer controller
observes recovery on a real process death. The live MAP01 allocation remains
uninvoked, and this result must not be promoted to integrated control success.
