# Independent recheck of PR #8290's EOF process-group cleanup repair

This package compares the same eight process-tree regression cases against the
base implementation and PR #8290's implementation on the same host/runtime.
The test file is copied byte-for-byte from the PR head and identified by its
Git blob in `RESULT.json`.

## H/T/D/C/U

- **H:** On this Darwin host, a completed but unreaped owned process-group
  leader can make `killpg(SIGTERM)` raise `PermissionError`; polling/reaping the
  leader before signaling, with one exit-race retry, should pass the same
  process-tree cases while preserving permission failures.
- **T:** Run the exact eight-case test file from PR #8290 once against the base
  source and once against the candidate source with the same Python executable,
  host, and inputs.
- **D:** Scoped support requires the retained base to fail in the reproduced
  conditions and the candidate to pass all eight cases; otherwise the repair
  remains unverified.
- **C:** The denied signal may instead reflect a different process-group state
  or platform behavior. The suite has mocked race/permission cases plus actual
  local child-process cleanup cases.
- **U:** This one host/runtime check does not test app-server protocol behavior,
  GUI/native input, gameplay, task effects, useful feedback, recovery efficacy,
  or an OS-wide shutdown bound.

On macOS 27.0.1 arm64 with Python 3.14.5, the base implementation produced two
errors and two failures among the eight cases. The reported EOF-close case
raised `PermissionError` from `os.killpg` for an exited, unreaped child. The
PR implementation passed all eight cases. The ordinary three process-tree
tests present on base passed in the baseline run.

This is a local regression recheck of one app-server client cleanup path. It is
not a live GUI, native-input, game, model, task-effect, useful-feedback,
recovery-efficacy, or OS shutdown worst-case result. It does not independently
approve PR #8290 or establish the Issue #59 live threat-exposure gate.

Run `python3 -B run_independent_recheck.py` from this directory to restore the
two source blobs from the pinned Git commits and execute the frozen test file
against each. Run `python3 -B audit_recheck.py` to validate the retained raw
outputs and their recorded disposition without rerunning the tests.
