# FORMAL FAILURE — frozen source absent from local execution directory

Allocation `INTENT-SLOT-6081-T0S2-20261001-01`; frozen source commit `628f4feafd08beeeaba1809801a4a56c5cbdbb44`; base `6cd70ad4bfad74e11658057bf024918bffb24add`.

**Disposition: `STOP_RUNNER_SOURCE_NOT_MATERIALIZED / NOT_EVALUATED`.** The wrapper argument canary passed, and the candidate command received the intended argv, but its working directory was the fresh S2 scratch folder, which contained only the S2 freeze receipt and not the source files. Python exited 2 before loading or executing `candidate.py`. Candidate CLI attempt=1; candidate module executions=0; auditor attempts/executions=0. No candidate or audit JSON exists. No retry or local copy-and-replay is permitted under S2.

## Exact evidence

- Candidate argv: `-B candidate.py --input cases.json --output formal/candidate.json`.
- Start/end: `2026-10-01T13:54:44.9832609Z` / `2026-10-01T13:54:45.0834299Z`; process elapsed 95.449 ms; exit 2.
- Captured stderr: 249 bytes, SHA-256 `303D7619ACABA990AE597FDFF2F0DE8CD1266BE5D501448E9EC7C8AAA22725CE`, reports that `candidate.py` is absent from the specified S2 working directory.
- Captured stdout empty, SHA-256 `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`.
- `formal/process_receipts.json`: SHA-256 `81F85910C9CB0201236833A58B0E7ADC539B89A20DB99661CBF84D1B4F57B10B`.
- `formal/candidate.json`, `formal/audit.json`, and auditor invocation receipt are absent.

## Containment

The exact frozen GitHub package exists at the S2 branch path, but the scratch working directory was not populated from that readback before launch. The failure is local source materialization/runner setup, not method evidence. S1 remains a distinct earlier argument-binding STOP. S2 source/freeze and both STOPs remain unchanged. Any new attempt requires a third distinct allocation with explicit local byte materialization/readback before its source freeze; do not rerun or repair S2 in place. No Docker, GUI, game, model, or physical input was used.
