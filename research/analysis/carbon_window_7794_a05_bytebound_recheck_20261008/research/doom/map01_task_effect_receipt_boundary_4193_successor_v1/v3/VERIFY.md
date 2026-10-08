# v3 verification record

Environment: CPython 3.12.10, standard library only. No Docker/OrbStack or live environment was used.

The exact `runner.py` and independent `audit.py` from code snapshot `fd206cb1cd0ff4948835afa7b9e9b4f120e032e4` were fetched from the experiment branch. The retained source was fetched from main; the runner verified its compressed-byte SHA-256 before decoding.

The runner checks exact session membership, scorer schema and within-session monotonicity, physical DOWN/UP brackets and adapter edges, nonempty receipt identities, and equality across DOWN/UP identity fields. Both scripts recursively inspect the complete retained session object for native `source_event_id` and `scorer_event_id` keys.

Executed sequentially in an isolated temporary directory:

```text
python -S -B runner.py RAW_USED.json.xz RESULT.json
python -S -B audit.py RAW_USED.json.xz RESULT.json
```

Observed:

```text
RUNNER_EXIT 0
{"attack_physical_joins_supported": 3, "attack_positive_endpoint_total": 0, "attack_sessions": 3, "attack_sessions_with_positive_scorer_endpoint": 0, "disposition": "HOLD_NO_POSITIVE_SCORER_EVENT", "native_scorer_event_id_present_anywhere": false, "native_source_event_id_present_anywhere": false, "noinput_positive_endpoint_total": 0, "noinput_sessions_with_positive_scorer_endpoint": 0, "scorer_sample_total": 194, "session_count": 6, "source_bytes": 7392, "source_sha256": "0d55f782f0e129738b422e52d8066f7fb69a02ebcf2c1691ee711e74a369a740", "study": "4193-retained-source-schema-compatibility-v3"}
AUDIT_PASS sessions=6 physical_joins=3/3 attack_positive_sessions=0/3 noinput_positive_sessions=0/3 scorer_samples=194 source_event_ids=absent scorer_event_ids=absent
AUDITOR_EXIT 0
```

This verifies publication artifacts and recomputes the retained-source schema facts. It is not a fresh experiment or independent task-effect replication. The historical #4193 first result remains unchanged.
