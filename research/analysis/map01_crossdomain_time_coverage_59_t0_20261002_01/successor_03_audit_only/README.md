# Cross-domain time-coverage audit-only successor

This package re-audits the immutable T0-02 candidate output; it does not run or regenerate a candidate. It counts absent event kinds as zero while preserving sparse event maps, verifies every candidate event-count map against source, and checks OpenTTD observer count and transition fields.

Run construction tests first:

```sh
python3 -B -m unittest -v test_audit_only
```

After checking `FREEZE.json`, invoke the raw-only audit once:

```sh
python3 -B run_audit_only.py
```

No container, model, game, GUI, OS input, or GPU is used.
