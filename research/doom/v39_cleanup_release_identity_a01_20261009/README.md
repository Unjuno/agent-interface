# V39 failure-cleanup release identity A01

Classification: offline construction regression and local repair for Issue #59.
No model, Doom process, GUI, OS input, live game allocation, or physical release
was used.

## H/T/D/C/U

- **H:** When a terminal release explicitly carries an `intent_token`, V39
  failure cleanup must not mark it as verified-empty for an accepted program
  whose accepted event carries a different token. Legacy terminal release
  objects that omit this optional field remain ID-bound and retain the existing
  behavior.
- **T:** Run the same three-case test against the exact current-main helper blob
  and the patched helper: matching token, mismatched token, and omitted token.
  Then run cleanup/source-refresh regressions, V39 controller tests, and
  pending-observation-drain tests normally and under `python -O`.
- **D:** The baseline is expected to fail only the mismatch negative control.
  The candidate must pass all three identity cases. All regression commands
  must exit zero. A mismatch is refused as a release certificate; no input
  action is admitted by this test.
- **C:** This is a synthetic event-receipt test around the production cleanup
  class. ID matching and protocol behavior are represented by test fixtures;
  this does not prove live owner behavior or physical key state.
- **U:** Windows CPython 3.11 was used. `wslc.exe` is unavailable and POSIX-only
  `send_failure_finish` behavior was not exercised. No controller exception was
  induced in a real Doom session; scorer completion, owner close, live source
  refresh, task effect, and MAP01 completion remain untested.

## Result

Against current main `d66ee6cd4f9c09387845bc0765855cbede0c0874`, the mismatch
case failed as predicted: cleanup reported
`input_release_verified_empty=true` although the release token differed from
the accepted token. The exact main helper blob is
`d04e167ed182d5faf935e6c23132b164fe9a16ac`.

The candidate rejects the explicit mismatch and preserves both exact-match and
legacy token-omission behavior (3/3). Cleanup/source-refresh tests passed 20/20
in both modes; V39 controller tests passed 16/16 in both modes; pending drain
tests passed 21/21 in both modes. `py_compile` and `git diff --check` passed.
The original POSIX pipe cleanup test was excluded from the Windows regression
matrix because its contract is POSIX-specific; its earlier Windows run failed
at the platform guard, not at a candidate assertion.

This result repairs only a false cleanup receipt when a token is explicitly
present and wrong. It does not turn missing token data into a lease proof and
does not establish physical release or overall controller cleanup completion.
Raw output, exits, freeze record, and audit are in this directory.
