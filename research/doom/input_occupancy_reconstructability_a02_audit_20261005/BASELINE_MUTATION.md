# Preserved A01 auditor false-pass control

Starting from the scratch-only replay of the committed A01 `RESULT.json`, the mutation set each run's reported physical-down count to its admission count, inserted fabricated down/up actuation IDs, and set the event-payload per-key-up count to the admission count. The raw input streams and A01 `exact_per_key_occupancy_reconstructable=false` / `FAIL_INSUFFICIENT_PER_KEY_EDGE_EVIDENCE` values were unchanged.

The unchanged A01 `audit_a01.py` returned `PASS_AUDITED_INSUFFICIENT_EVIDENCE`, with zero errors, for that inconsistent summary. The exact mutated result and audit output are retained beside A02's clean raw-derived audit. The original A01 `RESULT.json`, `AUDIT.json`, raw event logs, and A01 source are unchanged.

A02's `test_audit.py` reproduces the forged-count/ID condition against the new raw-derived comparator and requires a rejection. This mutation control tests summary-to-source integrity only; it says nothing about physical input or unsafe behavior.
