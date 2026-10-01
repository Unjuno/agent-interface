# Formal-01 result — Issue #6143 guard/proposal adaptation T0

Allocation: `GUARD-PROPOSAL-RISK-6143-T0-20261002-01`  
Related issue: [#6143](https://github.com/Unjuno/agent-interface/issues/6143)  
Result: **PASS_METHOD_SCOPED**

## Finding within the finite synthetic model

The candidate used exact rational tree enumeration; an independent auditor used a separate iterative replay and did not import the candidate. Both ran once in separate pinned, network-disabled containers; total retries were zero. The auditor replayed the frozen two-world/two-proposal decision tree, conserved total launch mass `1` in every cell, and reported no mismatch or error.

| Policy / guard | Risky-proposal fraction | Correct rejection of harmful proposals (TPR) | All-launched task harm | Unfinished | Expected proposals / retries |
|---|---:|---:|---:|---:|---:|
| Fixed conservative / on | 1/4 | 3/4 | 33/512 | 31/256 | 43/32 / 11/32 |
| Fixed conservative / off | 1/4 | 0 | 3/16 | 0 | 1 / 0 |
| Guard-induced aggressive / on | 3/4 | 3/4 | 117/512 | 79/256 | 49/32 / 17/32 |
| Guard-induced aggressive / off | 3/4 | 0 | 9/16 | 0 | 1 / 0 |

Under guard-on, the planted aggressive proposal policy raises task harm by `117/512 - 33/512 = 21/128` (about 0.1641), exceeding the preregistered 1/10 absolute materiality margin even though conditional rejection efficacy remains 3/4. The exact harm change is correctly reported separately from guard TPR, harm among admitted actions, refusal rate, retries, unfinished work, and abstract proposal-work units. The null control reproduces the fixed conservative arm and is not flagged; the protective control is also not flagged. A candidate-output harm mutation is rejected by the auditor test.

This is a *planted-mechanism method check*: the 1/4→3/4 proposal shift is stipulated in the fixture. It does not show that any real model observes, believes, or adapts to a guard, nor that guards cause risk compensation in Agent Interface. Proposal-work units are an abstract one-unit-per-proposal counter, not tokens, latency, money, or energy. No empirical safety, user, product, or runtime claim follows.

## Exact formal commands

Image: `python:3.13.5-slim@sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`. Each command used `--network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=16m`; `/work` was read-only and only `/out` (the formal output directory) was writable.

```sh
python /work/runner.py --input /work/fixture.json --output /out/candidate_result.json
python /work/audit.py --input /work/fixture.json --candidate /out/candidate_result.json --output /out/audit_result.json
```

Both exited 0. The candidate emitted all four cell/control summaries; the independent auditor emitted `PASS_METHOD_SCOPED`, `replayed_world_weight=1`, both negative controls accepted, planted compensation caught, and `errors=[]`. Raw JSON output files are retained in `runs/formal-01/`.

## Reproducibility and limits

`FREEZE.json` binds the allocation to main `981ba1e`, the exact fixture/source hashes, container digest, resource policy, and decision gates. `RUN.json` records commands, observed summary, invocation counts, and raw-output hashes. Construction checks (8 tests, including a mutation rejection; `py_compile` pass) are separate from the formal result. The finite result assumes the declared world mix, per-proposal independent guard draws, two-proposal cap, and deterministic completion/harm oracle. Different task-state feedback, adaptation mechanisms, dependence, or guard visibility can change the estimand. T1 model cards and T2 live comparison remain unrun and separately gated.
