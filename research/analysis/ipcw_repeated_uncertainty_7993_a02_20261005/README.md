# Issue #8049 A02 — STOP

The first frozen A02 formal command was rejected by Docker's CLI because the runner supplied `rw` as a bare `--mount` field. No candidate container/process or auditor ran. The one-shot STOP and exact stderr are retained in [STOP.md](STOP.md), [RUN_RECORD.json](RUN_RECORD.json), and `results/candidate.stderr.txt`. A02 does not test or decide the interval hypothesis; it is not retried.

The fresh-seed bootstrap-method successor is stored separately in [`successor_a03_seed8049021/`](successor_a03_seed8049021/README.md). A01's coverage failure remains unchanged. No live verifier, GUI, safety, or production calibration claim is made.
