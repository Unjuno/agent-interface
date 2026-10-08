# Invocation log — allocation -04

This is a human-readable transcription of the returned Docker CLI statuses; the
container JSON/raw/audit files remain the machine-readable evidence. All calls
used the exact commands frozen in `FREEZE.json`, `--pull=never`, network none,
read-only root/source and dedicated output mounts. No invocation was retried.

## Construction

- Exit 0; `CONSTRUCTION_STATUS=CONSTRUCTION_PASS EXIT=0`.
- Seven tests passed, including candidate and independent-oracle parity on all
  12,288 retained predictions.
- Receipt: `results/construction-04/construction.json`; its stdout/stderr logs
  are in the same directory.

## Formal

- Exit 0; `PILOT_STAGE=preflight STATUS=PASS`.
- Fifteen block checkpoints completed in order: 1/15 through 15/15.
- Terminal status: `PILOT_STATUS=RUN_COMPLETE ROWS=30000`.
- Durable per-block raw checkpoints and all predictions/timings:
  `results/formal-04/raw.json`.

## Independent raw-only audit

- Separate invocation; raw mounted read-only; exit 0.
- Terminal status: `AUDIT_STATUS=PASS_LIFECYCLE_AMORTIZATION_SCOPED ROWS=30000 WINS=15/15 MUTATIONS=7/7`.
- Machine-readable independent reconstruction and metrics:
  `results/audit-04/audit.json`.
