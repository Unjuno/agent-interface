# Issue #4990 frozen local protocol

Allocation: `typed-negative-outcomes-opt-check-39-20260928-01`; source branch `research/typed-negative-outcomes-opt-check-39-20260928`. Main intake commit: `7d1208cf323408897983ef2b5c75fd34f54d6815`. Immutable predecessor input: `research/analysis/typed_negative_outcomes_successor_39_v1/contract.py`, blob `e9c447f02e6652369455959fe1b5f5dece31876e`.

## Hypothesis / treatment
The old contract uses `assert` for hard decision gates. Candidate `candidate.py` replaces those gates with explicit fail-closed exceptions and binds exact 384-row output digest/counts. All other state-space semantics and precedence are unchanged. A frozen standard-library oracle and independent raw-only `audit.py` check the subprocess outputs. Seven declared corruption controls per interpreter mode are required to fail before any PASS marker.

## Frozen environment and invocation
Use cached image `python:3.12-slim-bookworm`, exact local image ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, platform linux/amd64, Python 3.12.14. No pull, network, package installation, GPU, model, GUI, runtime write, or hosted workflow. Root filesystem and source/input are read-only; only a fresh per-allocation output mount is writable; CPU <=0.25, memory <=512 MiB, PIDs <=32, tmpfs /tmp <=16 MiB.

Construction tests are excluded from the one formal test block. Freeze SHA-256 for predecessor input, README, protocol, candidate, preformal test, and auditor; verify GitHub readback before container invocation. Then run each valid case once in ordinary Python, `python -O`, and `PYTHONOPTIMIZE=1`, and each of seven frozen invalid-output controls in all three modes. Retain stdout/stderr/exit receipts and exact JSON lines. The auditor runs after collection and independently checks mode, gates, digest, rows, counts, failure-before-pass, and zero authority. Use a new empty output directory. One invocation only; preserve any failure without retry.

## Decision
PASS only if the predecessor digest and exact counts match in all three interpreter modes, every declared invalid candidate is rejected in all modes before PASS, and the independent auditor reports zero errors. A bypass is `FAIL_OPTIMIZED_GATE_BYPASS`; source/image/output/audit defect is `STOP/HOLD`, not a scientific pass.

## Limits
One finite seven-boolean state space, three CPython modes, one cached Docker image and host. This establishes neither runtime authority nor planner/model/GUI behavior, task quality, latency, deployment safety, or general security.

## Construction inventory status
Candidate/preformal test/auditor files have been added to the dedicated branch. Formal count remains zero. Preformal test execution, full corruption runner, source digest ledger and read-back freeze remain pending; formal entry is prohibited until all four finish.
