# Cross-domain time-coverage successor T0-02

This additive successor preserves T0-01's candidate and audit failure. It fixes only the output count labeling and auditor predicates, then runs a new, one-shot deterministic replay against the same immutable source traces under a new allocation.

From this directory in the retained package, first run:

```sh
python3 -B -m unittest -v test_candidate_v2 test_audit_v2
```

After source/input collision and hash checks, execute exactly once:

```sh
python3 -B run_candidate_v2.py
python3 -B run_audit_v2.py
```

The second command is allowed only after the candidate exits 0. It imports no candidate code and compares all candidate event counts with independently parsed source counts, including the v38 score row that failed T0-01. It also verifies distinct raw observer records (263) and transition witnesses (1), rather than aliasing them.

No container, live application, model, GUI, OS input, game, or GPU is involved. This only validates historical evidence classification and the conservative HOLD disposition.
