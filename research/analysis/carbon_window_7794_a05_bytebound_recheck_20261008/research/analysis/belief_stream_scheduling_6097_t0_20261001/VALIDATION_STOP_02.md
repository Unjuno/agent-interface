# Validation rerun STOP 02 — test harness cost

This post-freeze validation attempt did not change official candidate, auditor, protocol, tests, raw data, or the decision gate.

- Current committed `results/formal-01/RAW.jsonl` was independently audited with the committed `audit.py`; it returned `FAIL_AUDIT`, exactly `heldout_miss_improvement`, exit 1. This confirms the official scoped FAIL from the retained raw.
- A fresh invocation of committed `python3 -B -m unittest -v test_scheduler.py` generated its own construction raw and passed the first two tests (`age_is_not_monotonic_uncertainty_rank`, `auditor_rejects_metric_mutation` had not completed; the observed first test passed, and the second began). It was interrupted after about two minutes while the metric-mutation test repeated the 4,096-world exact replay. Exit 130. No complete test-suite result is claimed.
- This is a validation-harness runtime STOP, not a new scientific outcome. The existing unit tests that previously completed remain construction evidence only; the focused suite has no current all-tests pass.
- Current PR review list is empty; GitHub's automatic code-review comment says the account reached its code-review usage limit. Hosted Actions remain queued, so neither hosted success nor reviewer approval is established.

Disposition: `STOP_TEST_SUITE_COST`; do not rerun this unchanged expensive suite. A future validation-only optimization must preserve official source hashes and prove equivalent test coverage before it can be reported as complete.
