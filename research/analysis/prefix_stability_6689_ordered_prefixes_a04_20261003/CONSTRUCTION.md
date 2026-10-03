# Construction checks — A04

Before the final freeze commit `5220f420f0a21f500e4a96bb63004bc740ace951`, the host-side construction command

```text
python -B -m unittest -v test_method.py
```

passed 9/9 tests. These checks exercised the deterministic method and in-memory corruption controls; they did not invoke either formal CLI. The test names were:

1. `test_complete_failure_does_not_wait_for_optional_source_or_seal`
2. `test_disposition_counts_are_exclusive_and_metrics_separate`
3. `test_each_trace_contains_every_prefix_once`
4. `test_incomplete_negative_keeps_the_pending_obligation_after_seal`
5. `test_independent_raw_oracle_matches_candidate_construction`
6. `test_positive_waits_for_generation_seal`
7. `test_same_terminal_results_have_distinct_intermediate_histories`
8. `test_six_frozen_mutations_are_rejected`
9. `test_trace_and_prefix_cardinality`

After the pre-formal timestamp correction, the same 9/9 construction checks passed again. The corrected frozen wrapper imported successfully, and every source/input SHA-256 matched `FREEZE.json` before launch. The formal candidate and auditor were then each invoked once under WSLc; see `RUN.json` and the retained container receipts.

After main integration, a separate test-discovery command was accidentally issued from the repository root, where `test_method` is not an importable top-level module; it failed before running any test. The command was immediately rerun from this package directory and passed 9/9. This was a test-path error only and did not invoke either formal CLI.
