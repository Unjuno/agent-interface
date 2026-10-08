# Blackwell information vs deadline-dependent action value — Issue #5329

## Result

`METHOD_PASS_SCOPED`: in this authored two-state decision simulator, RAW_NOW has expected utility 6, COMPRESSED_NOW 2, and both delayed arms 0. Thus raw strictly exceeds compressed at equal arrival, while compressed-now exceeds raw-delayed after the deadline. Both compressed irreversible-commit probes are refused; all five corruption controls are rejected by the independent auditor.

This is a finite decision-theoretic construction only. It is not empirical evidence about GUI capture, transport latency, a real agent, task success, or product behavior.

## Frozen allocation

- Issue: [#5329](https://github.com/Unjuno/agent-interface/issues/5329), freeze comment 5924272957
- Allocation: `5329-blackwell-deadline-t0-20261001-01`
- Base: `f0d5aa9d7fb73e5801f8d6190009e56c72583057`
- Branch: `research/5329-blackwell-deadline-t0-20261001`
- Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
- Local Docker: network none, 1 CPU, 256 MiB, pids 64; preflight, runner, auditor each run once.

## Reproduction

The frozen source is `runner.py`, `audit.py`, and `test_preflight.py`. Run preflight read-only first. The formal runner requires a new empty `/out/formal01`; do not rerun this consumed allocation. Then run the independent auditor once against its `raw.json`. Exact commands, outputs, exit statuses, and hashes are retained in `results/formal01/execution.txt`.

## Evidence

- `results/formal01/raw.json` — immutable 8-row first outcome
- `results/formal01/audit.json` — independent recomputation and 5/5 corruption controls
- `results/formal01/execution.txt` — allocation provenance, image/limits, invocation statuses and SHA-256 identities

No runtime changes. Follow-up empirical transport or GUI work requires a separately frozen successor allocation.
