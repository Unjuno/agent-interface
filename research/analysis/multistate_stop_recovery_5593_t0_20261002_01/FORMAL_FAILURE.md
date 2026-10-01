# FORMAL_FAILURE — Issue #5593 multistate T0

Disposition: `METHOD_FAIL_AUDIT`; the frozen independent-auditor gate failed and the allocation was not retried.

Candidate was invoked once and exited 0 with 5 episodes / 6 ticks; raw output SHA-256 is `83997cc3799812cb71ef44194c961ab3a7a50cafb3266f4398b80fc1738c64da`. The auditor was invoked once and exited 1 with `ValueError: mutation not rejected: omitted_episode`; no audit artifact was produced.

Cause: the omitted-episode mutation was reconstructed from its shortened ledger and the audit harness accepted that input's own reduced `launched_n`. The audit therefore lacked an independently frozen expected launch roster. Construction had passed 11/11 but missed this weakness. Source, fixture and candidate raw remain preserved; no rerun is permitted. Exact identities and limits are in `FREEZE.json`, `RUN.json`, `FAILURE.md`, and `SHA256SUMS`.

This is a synthetic method-audit failure, not an empirical task-cohort result or evidence of real-world behavior. A distinct successor on a new allocation added the missing frozen-roster boundary; see sibling `multistate_stop_recovery_5593_t1_20261002_02/`.
