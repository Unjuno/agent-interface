# A07 construction-only gate

- Host command: `python3 -I -S -B -m unittest discover -v -s research/analysis/dual_control_5309_witness_a07_20261007 -p test_construction.py`
- Result before freeze: 4 tests passed; six raw-corruption probes were all rejected.
- `candidate.py` and `candidate-input.json` contain no oracle truth mapping or hidden-state label. The test verifies this source/input boundary and joins opaque case IDs to oracle truth only in the separate auditor test harness.
- Candidate mount smoke: one initial construction-only command failed before container start because its `out/` source path contained a transcription typo; exit 125, no candidate invocation, no output. Corrected smoke passed with `CANDIDATE_MOUNT_ISOLATION_OK`, confirming candidate code/input are visible and `/input/oracle.json` is absent.
- Auditor mount smoke: one initial construction-only command likewise failed on a hand-typed source-path typo, exit 125 before start. Corrected variable-based command passed with `AUDITOR_MOUNT_ISOLATION_OK`, confirming the auditor sees the oracle and candidate input while candidate source is absent. These were environment/mount assertions only, not formal candidate/auditor calls.
- No container cleanup, existing-state mutation, model call, GUI call, input authority, or scientific claim.
