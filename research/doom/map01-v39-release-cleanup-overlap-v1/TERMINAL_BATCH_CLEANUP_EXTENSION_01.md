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

Based on PR #7395's malformed-evidence hardening head
`b17d492aee852e7eff114fb0f4a7d3dcb0531ee7`, itself based on refreshed #7385.
The test
extracts and executes the actual `Backend.release_all` method from
`research/live_control/session_v5.py` in an isolated test parent (avoiding GUI
imports). It exercises a final buffered batch, an unverified terminal cleanup,
a malformed cleanup timestamp, overlap within explicit-up brackets, and a valid
cleanup record predating the current batch.

## D — Data and execution

- Candidate Git revision: `81a528694fa59d195e91dab8703492abf04aea93`.
- Baseline adapter at #7395 head: SHA-256
  `5478a4bde87f59db545818e30f31f0afb4934bb5851e441eebf8136b49639a0e`.
- Baseline test at #7395 head: SHA-256
  `eaa8fe562393c9534fc7df62f9262637c7c5e9c26b67c22802e71cbd349ae791`.
- Candidate adapter: SHA-256
  `895fd4c5edbb09e2f843ddc20a74d569d4196c9aba9654c870f0dafadd11d4d6`.
- Candidate test: SHA-256
  `1cba55ec4b37fd697baaabc8690935004ec88bf30c640f1c8e124225294eba5d`.
- `python3 -B -m unittest -v test_doom_typed_release_backend_v3`: **27/27 PASS**.
- `python3 -B -m unittest -v test_input_transition_owner_v3`: **8/8 PASS**.
- `python3 -B -m unittest -v test_overlap_controller_v39_wait`: **7/7 PASS**.
- `git diff --check`: PASS.
- `python3 -B` source compilation: PASS.
- Exact-parent RED: `python3 -B
  research/doom/map01-v39-release-cleanup-overlap-v1/run_terminal_cleanup_parent_red.py`
  loads backend source at `b17d492a`, runs the terminal flush regression, and
  observes the expected `[] != ['a']` assertion (1 failure, 0 errors). Its
  script exits 0 only for that exact expected failure; raw output and JSON
  receipt are retained.
- Candidate rerun: `python3 -B
  research/doom/map01-v39-release-cleanup-overlap-v1/run_terminal_cleanup_candidate.py`
  retained stdout/stderr for all 42 tests. The separate
  `audit_terminal_cleanup_candidate.py` rechecks source hashes, raw-log hashes,
  exact suite counts, terminal summaries, exits, and the parent RED receipt:
  **PASS**.
- Current container gate: STOP. Docker server reports OrbStack 29.4.0, but
  `docker version --format '{{.Server.Version}}'` succeeds and read-only
  `docker ps --format '{{.ID}} {{.Image}} {{.Status}}'` fails on content blob
  `sha256:08e8b41ebd1476eff067939e0192d49e4014c21bab11a4d793429187e4242704`
  with `operation not supported`; image inventory and container execution were
  not attempted after that failure. No repair, pull, or live allocation ran.
- A few initial test invocations used an unavailable module name or wrong
  working directory; corrected commands passed. These were setup errors, not
  product failures.
- Candidate refreshed onto #7395 after discovering parallel malformed-log and
  bracket coverage on the same backend; combined tests retain both sets.
- Retained run records: `CANDIDATE_RUN.json`, `PARENT_RED.json`, and
  `RAW_*_TESTS.txt` / `RAW_PARENT_TERMINAL_RED.txt`.

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
