# V39 current-main affected-suite regression A12

The exact `main` source at `a6343bb76e4dc0a4afa32a29c8a485a617faeff8` passed four model-free V39/controller suites in normal and optimized Python 3.13.14: controller 16/16, pending-observation drain 22/22, final-action admission 9/9, and running-action guard 7/7. Candidate suite execution and independent source/result audit both passed. All 54 tests passed in each mode (108 executions).

The first A11 attempt used A10's stale expected counts (15 controller, 20 pending drain). It retained a harness-level `FAIL` despite all executed tests exiting 0; exact actual counts were 16 and 22. A11's raw output and dated disposition remain unchanged. A12 prospectively freezes the corrected counts and independently verifies exact Git blobs, SHA-256 values, run receipts, counts, and `OK` endings.

This is deterministic source-level regression evidence only. It does not establish live threat exposure, useful feedback, physical key release, recovery, survival, or MAP01 exit, and it does not satisfy Issue #59's live gate. No game, model, GUI, OS input, WSLc, Docker, or container was invoked.

Before publication, `main` advanced two commits to `57337e95ecbecf7e762c8ec8091472b79e8ad49f`. An additive byte-identity carry-forward check verifies all 34 pinned test/import source blobs are unchanged at that tip and that no changed path overlaps the pinned closure; this supports continued source applicability without claiming a rerun at the new tip.

See [`README.md`](README.md), [`FREEZE.json`](FREEZE.json), [`RESULT.json`](RESULT.json), [`MAIN_CARRY_FORWARD.json`](MAIN_CARRY_FORWARD.json), [`audit.py`](audit.py), and [`SHA256SUMS.txt`](SHA256SUMS.txt). The A11 failure and diagnostic are retained separately.
