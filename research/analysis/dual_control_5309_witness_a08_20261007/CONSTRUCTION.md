# A08 construction-only gate

- Host command: `python3 -I -S -B -m unittest discover -v -s research/analysis/dual_control_5309_witness_a08_20261007 -p test_construction.py`
- Result before freeze: 4 tests passed; six raw-corruption probes were all rejected.
- `candidate.py` and `candidate-input.json` contain no oracle truth mapping or hidden-state label. The test verifies this source/input boundary and joins opaque case IDs to oracle truth only in the separate auditor test harness.
- Exact registered launchers were exercised in `smoke` mode before freeze: candidate printed `CANDIDATE_MOUNT_ISOLATION_OK`, auditor printed `AUDITOR_MOUNT_ISOLATION_OK`. The scripts resolve their own allocation root, eliminating hand-copied bind source paths. Smoke checks are construction-only and do not invoke the candidate or auditor modules.
- Earlier A07 hand-command mount typos are preserved in A07 `CONSTRUCTION.md`/`STOP.md`; they do not modify A08.
- No container cleanup, existing-state mutation, model call, GUI call, input authority, or scientific claim.
