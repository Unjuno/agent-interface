# R05 assessment

**Outcome: `FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED`; no dispatch input was sent.** The owned Win32 fixture started as PID 16132, was visible/enabled/foreground, and had `SHIFT-up`. Native preflight generation `f59e1f0f…e89df` matched the generation shown inside the public observation's raw report. The runner compared against the outer receipt-view wrapper, which omits that field, and stopped before dispatch. The observed public raw report itself says `status=returned`, `target_generation_consistency=matched`, and `input_dispatched=false`.

Post-run custody confirms zero action calls, no unresolved calls, the fixture exited with code 0, no effect file was created, and foreground restoration returned to the original HWND. SHIFT remained up. The close receipt's `release_confirmed=false` describes a close with no active input obligation and is not treated as a release failure.

All raw files passed their retained SHA-256 manifest check; frozen conditions, preregistration, and runner also match `PRETRIAL_SHA256SUMS`. This setup failure is immutable. The corrected R06 parser extracts the retained raw report from the public receipt wrapper; R06 has a new attempt ID and is the only permitted follow-up.

## Boundary

R05 tested only the runner's no-input generation preflight. It provides no blocked-I/O recovery, task effect, or release result. No WSLc, Docker, or AppServer provider was used.
