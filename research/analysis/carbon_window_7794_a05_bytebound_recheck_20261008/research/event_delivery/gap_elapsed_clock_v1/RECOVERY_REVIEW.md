# Recovery review — Issue #3986

## Decision and provenance

This is an additive recovery of the unmerged `research/gap-elapsed-clock-926-20260922-isolated` branch. Its completed allocation predates the GitHub Issue and branch. Preserve that chronology as recorded in `PUBLICATION_NOTE.md`; this recovery does not retroactively describe the run as GitHub-preregistered.

The original two-part addition-only patch reconstructs to 2,025,006 bytes with SHA-256 `3eebe00328aab0f7d6abfb1ab6c6f41b0795abdc09de2d92e2185a4fd8b4fb75`. It restores 450 files. Against the current main, 440 files were absent and 10 were already present byte-for-byte; there were no conflicting paths. The five original publication-transport files not contained in the reconstructed patch are retained unchanged alongside it.

## Recovery validation

- Reconstructed the original patch in an isolated temporary tree and verified its recorded SHA-256 and 450-file count.
- Verified the original `SHA256SUMS`: 449/449 listed artifacts matched.
- Independently audited the retained formal raw evidence: `PASS_LOCAL_CLOCK_BOUNDARY_SCOPED`, 72/72 cases, with no audit errors.
- Ran the copied-evidence mutation controls: 11/11 corruptions rejected; the control harness reports that original evidence was not modified.
- Ran the policy unit tests: 8/8 passed.
- No formal allocation, worker, batch, or Docker experiment was rerun. The audit ran under local CPython 3.14; the retained allocation metadata records Linux x86_64 / CPython 3.13.5 / SQLite 3.46.1.
- The preserved historical `INHERITANCE.diff` has one whitespace-only added line at line 9; `git show --check` reports it. It is retained byte-for-byte rather than silently rewriting the evidence artifact.

## Interpretation boundary

The recovered result supports only the scoped notification eligibility comparison under the recorded polling schedules. It does not select 80 ms as a production default, guarantee a wall-clock deadline or wakeup when polling stops, validate a production producer/presentation path, or establish model-useful-feedback or product impact. Issue #926's observation-count contract remains valid within its stated scope.
