# A16 posthoc independent raw cross-check

This supplemental check re-read A16's frozen ledger, query oracle, prompt templates, model request records, and preserved raw JSONL. It did not invoke the registered auditor or any model. `verify_raw_crosscheck.py` reconstructs each expected memory state from the episode ledger, checks every consolidation request and result, replays the actual memory state into every query prompt, verifies model identity and decoding settings, and independently recomputes exact-answer scores.

The check covered all 390 rows, 30 consolidation transitions, and 360 query responses. It found zero transition mismatches, malformed query responses, request/evidence mismatches, identity/settings mismatches, or score mismatches. The per-seed exact-answer scores match the frozen audit JSON, whose status is `PASS_METHOD` with zero errors. Machine-readable output is in `INDEPENDENT_CROSSCHECK.json`; rerun from this package with `python3 verify_raw_crosscheck.py`.

This is posthoc corroboration of A16's finite raw and formal audit. It does not add seeds, independently replicate the corpus, validate the researcher's hypothesis beyond this fixture/model, or support GUI/product/action-effect claims. A17's 8B run failed its separate method gate, and A18's new-seed replication stopped incomplete because the host ran out of disk space; neither is pooled here.
