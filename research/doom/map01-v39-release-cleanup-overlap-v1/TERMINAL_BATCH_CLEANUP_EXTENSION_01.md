# Terminal cleanup extension 01

Status: candidate PASS for the synthetic contract; container and live-control
gates STOP/not run. This is additive to the existing cleanup-overlap evidence;
it does not replace or rewrite predecessor results.

## H — Hypothesis

When `session_v5.Backend.release_all()` releases keys at program termination,
buffered per-key release receipts can be lost because production cleanup calls
the owner directly rather than iterating through `raw()`. In addition, malformed
or unverified cleanup records must not support an ordinary-release claim.

## T — Test

Based on the refreshed PR #7385 head
`90e65c932a8a487d9657713e5a243cba25125c4f`. The test
extracts and executes the actual `Backend.release_all` method from
`research/live_control/session_v5.py` in an isolated test parent (avoiding GUI
imports). It exercises a final buffered batch, an unverified terminal cleanup,
a malformed cleanup timestamp, overlap within explicit-up brackets, and a valid
cleanup record predating the current batch.

## D — Data and execution

- Baseline adapter at refreshed #7385 head: SHA-256
  `df7ea1c1ec2f1ce05e380b35586e0601b06ad591cb52be0702e0f4278cb65a2a`.
- Baseline test at refreshed #7385 head: SHA-256
  `eb7c6db10369e843b82f76fb26e8ce266c3334994e2e58546513f8986fd69e65`.
- Candidate adapter: SHA-256
  `fa9c72beb838ceceff117408f6d88f2b02dc1d8d3102b3295428ad6e571b2731`.
- Candidate test: SHA-256
  `03189f87ea22a53a27c2f8d2a82d9fafbd74c2c17e0823256ad4d2612ec0b9bd`.
- `python3 -B -m unittest -v test_doom_typed_release_backend_v3`: **24/24 PASS**.
- `python3 -B -m unittest -v test_overlap_controller_v39_wait`: **7/7 PASS**.
- `git diff --check`: PASS.
- Container execution: STOP. OrbStack/Docker image inventory had previously
  failed while reading a content blob (`operation not supported`); no repair,
  image pull, container, or live allocation was attempted in this run.
- `test_input_owner_v11`: not run; import is unavailable because this Python
  environment lacks `python-xlib` (`No module named 'Xlib'`).
- Initial setup used unavailable module naming/working directories; corrected
  invocations then passed. These were setup errors, not product failures.
- After refreshing onto #7385's newer head, the targeted suites and compile
  check were rerun and passed again.

## C — Conclusion

Synthetic evidence supports publishing the terminal buffered receipt after the
single post-cleanup owner-state sample. Records are scoped from the first
explicit release call's pre-call record count, so prior valid cleanup history
does not invalidate the current batch. A malformed cleanup timestamp, failed
cleanup, non-empty owner state, or unverified terminal cleanup prevents
`owner_transition_verified`. This is telemetry/owner-state evidence only; it
does not establish physical release, GUI safety, real-time deadline guarantees,
or Issue #59's matched threat-control gate.

## U — Uncertainty and next gate

Run the complete relevant suite in the prescribed container with retained image
identity, then independently review the PR on its final head. Restore Xlib for
the owner wrapper suite, and only after the exclusive live allocation gate is
granted proceed to the bounded, non-destructive experiment specified by the
current roadmap. No live claim is made here.
