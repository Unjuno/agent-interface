# Frozen preregistration — #3442 retained-result independent audit

Allocation: `intent-aligned-system1-3442-audit-localdocker-01`
Governing Issue: #3849; source idea #3442; immutable predecessor Draft PR #3738
Fresh branch: `research/issue-3849-intent-audit-docker-v1`
Base main commit: `d158286a3d5a0a1f420fc09fb831add8ead43791`
Predecessor source commit: `61a5676a45844e789a49ea99bdcf0ddf7bd835dd`

## H — Hypothesis

The retained held-out output and serialized weights from #3442 can be independently re-evaluated with a standard-library-only auditor under a 256 MiB container memory limit. It will reproduce recorded teacher labels, paired intent ordering, both model predictions, aggregate metrics and FAIL/HOLD gate disposition without importing PyTorch or rerunning training.

## T — Frozen audit

- Inputs are exact predecessor bytes copied under `intent_alignment_3442_pilot_01/`: `PREREG.md`, `CONSTRUCTION.md`, `runner.py`, `audit.py`, `RESULT.json`, `RESULT.md`.
- The new scalar forward pass reads serialized 6-32-32-4 weights and independently recomputes the 1,024 baseline and conditioned predictions; no model training or optimizer update occurs.
- The complete held-out record is checked for 512 ordered same-state pairs (intent 0 then intent 1), independently computed teacher labels, both prediction vectors, accuracy, paired exact accuracy, latency p95, decision gates and outcome.
- One formal audit invocation only. A stdout mismatch, prediction mismatch, resource failure, or source/image mismatch is retained as the first result; no retry, replacement, tuning, CUDA, GUI, task input, network, or GPU use.
- Before formal execution, construction checks were run on the host and in local Docker. The Docker construction suite exercises six cases: unchanged hold reconstruction, incorrect raw digest, altered prediction, forged gate, forged outcome, and pair-order corruption.

## D — Decision

`PASS_AUDIT_INTENT_ALIGNMENT_HOLD_SCOPED` requires exact frozen source/result hashes; all 1,024 rows, pairing, labels, predictions, metrics, gates, and outcome reconstructed with zero errors; all frozen corruption controls rejected; and one formal audit completed within the specified limits. Numeric model-quality misses remain misses and the predecessor outcome remains `HOLD_OR_FAIL_GATE_MISS`. Other first outcomes: `FAIL_AUDIT`, `HOLD_NUMERIC_RECONSTRUCTION`, `STOP_SETUP`, or `HOLD_RESOURCE_BOUND`.

## C / U

Local Docker Desktop Engine 29.8.0, Linux/amd64, cached image `python:3.12-slim` ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; `--pull=never --network none --read-only`, read-only source bind, 16 MiB `/tmp`, 32 process limit, 256 MiB memory, 2 CPUs. Exact command and input hashes are frozen in `FREEZE.json`.

Posthoc audit of one existing synthetic CPU training result only. It does not independently regenerate the PyTorch PRNG split, validate optimizer execution, establish real-task intent alignment, or convert the recorded predictive gate misses into a model PASS. No local training experiment is part of this allocation.
