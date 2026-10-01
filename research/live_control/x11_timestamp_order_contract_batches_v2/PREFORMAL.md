# #2802 allocation 02 preformal commitment

Formal state: **0/24**. No `FORMAL_CONSUMED` marker or `formal-02/` directory exists at freeze.

Predecessor allocation `x11-timestamp-order-20260922-01` remains immutable `STOP_CASE`: 3 complete, 1 partial, 20 unstarted. No predecessor row is pooled or resumed.

Excluded construction completed one case per frozen scenario (6/6), all case exits 0, no timeouts. Case durations were 2.187–2.733 seconds; maximum 2.733238193 s. This construction only validates the changed execution envelope. It is not formal scientific evidence.

The six scientific files (`actor.py`, `case.py`, `policies.py`, `upstream_monitor.py`, `audit.py`, `test_policies.py`) are byte-identical to allocation01. The changed files are only `run_batch.py`, `aggregate.py`, execution PLAN/environment/freeze metadata. Formal schedule, X11 operations, event semantics, thresholds and audit decision gates are unchanged.

Frozen allocation: four consecutive immutable six-case batches, case timeout 8 s, batch internal deadline 38 s, batch invocations exactly once in order. After all four batches complete, `aggregate.py` creates the 24-case RUN.json and the unchanged audit is run. Missing/incomplete batch is STOP/HOLD; no retry, replacement or partial PASS.

Freeze SHA-256: `f8a5b6f5b5e09baf5e5cf0d8392f12ac7951957c29bedf5202d1976dda5803c8`.
Source-only tar.xz: 13,040 bytes; SHA-256 `21a0e0ebeaae1c091a868f11843c9797b153048d1736fe435422ded14e2dadcd`.
Pre-freeze units: 10/10 pass. Formal reruns/replacements/tuning: 0/0/0.
