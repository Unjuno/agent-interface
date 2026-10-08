# Caller execution-progress regression: current main vs PR #7234

Status: `PASS_SOURCE_REGRESSION_SCOPED` for the PR-head change; current main
fails the new regression. This is an offline adapter test, not desktop-control,
model, latency, efficiency, or task-effect evidence.

## Frozen inputs

- Current main: `abb6f6f9c71f7c61db77070f0ced3c4bc2439dcd`.
- Current-main `research/live_control/adaptive_acquisition_caller_v3.py` SHA-256:
  `8517d130d7336b27e6ddfc0ee06629d2b1183070cf845c3ef4ada8adc3cd79ca`.
- Candidate: PR #7234 exact head `52d6b295c68e6c175d25aa9f52a58936c341983f`.
- Candidate caller SHA-256: `77cf5905c48ff4302d32007eeff5e75fcdbd5b2c5d88b00ec8d3def51b529130`.
- Python dependencies and runtime imports are from the checked-out repository;
  tests use plain deterministic adapters and no external services.

The regression asks whether a completed execution receipt remains observable
when the later effect verifier returns `failed` or `unavailable`, including
when terminal journaling itself fails. It also checks that the result remains
`TASK_NOT_VERIFIED` or `CALLER_FAILED` as appropriate, retains confirmed
delivery, records one execute and one verify, and grants no additional input
authority.

## Result

The pinned PR candidate passes all 14 available caller tests in both normal and
optimized Python. Against current main, the new regression produces two
assertion failures (the receipt is null for healthy terminal journaling) and
two errors when terminal journaling fails; the fallback attempts the same
failing terminal journal and lets the exception escape. The old behavior is
therefore a concrete current-main integration gap. The candidate's changed
branch preserves the detached completed receipt and passes all four new cases.

Run `python3 research/integration/caller_progress_7234_diff_20261004/reproduce.py`
from the repository root to fetch the exact PR-head files, run both candidate
modes and the current-main control, and write raw stdout, rows, and hashes.
Then run `python3 research/integration/caller_progress_7234_diff_20261004/audit.py`
to independently check the captured outcomes. The report does not qualify PR #7234
for merge; it remains a draft awaiting non-author review. It does not close the
separately gated #3311 live efficiency allocation.
