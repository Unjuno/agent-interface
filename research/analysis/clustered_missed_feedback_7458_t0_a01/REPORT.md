# A01 construction result (retained)

The first construction used |x|>4.0 as the unsafe boundary. It enumerated 24 schedules and recorded no unsafe cases in either split, so it did not exercise the hypothesis. The auditor independently reconstructed all 24 rows. This is retained as a failed construction boundary and was not pooled with A02.

Reproduce with `python -B research/analysis/clustered_missed_feedback_7458_t0_a01/runner.py` followed by `python -B research/analysis/clustered_missed_feedback_7458_t0_a01/audit.py`. Both exited 0. Scope is native host construction only; WSLc parity is unverified.
