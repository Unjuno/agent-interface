# Preserved first outcome — allocation 01

The frozen candidate ran once in the pinned local Docker container and exited 0. It emitted 4,373,672 bytes of raw event ledger. The separately invoked independent auditor ran once and exited 1 at its backlog reconstruction assertion.

First discrepancy: `high-abrupt_breaker-00`, tick 64 (and subsequent ticks). Candidate code injects a synthetic exogenous backlog jump with `backlog=max(backlog,9)` but does not record the jump as an event field. The auditor correctly cannot reconstruct the observed backlog from the recorded demand, injected delay and service alone. Therefore allocation 01 disposition is `FAIL_CONSTRUCTION_EVENT_LEDGER_INCOMPLETE`; it is not a scientific FAIL/PASS about recovery sentinels. No rerun was made. `raw.json`, stdout, exit receipts, frozen source and hashes are preserved unchanged.

Candidate stdout and raw were byte-copied before audit. Docker run used network none, one CPU, 256 MiB, 64 pids, pinned `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; Docker Desktop 29.8.0, linux/amd64. Both containers were `--rm`; no container remains.

