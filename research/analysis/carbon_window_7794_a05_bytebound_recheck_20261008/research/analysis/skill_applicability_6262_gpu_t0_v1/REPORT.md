# Issue #6262 — GPU-assisted T0 applicability certificate

## Result

**`PASS_METHOD_SCOPED`.** The frozen CUDA candidate enumerated all 4,096 evidence subsets over 12 feasible full cells and 23 feasible pair projections. A separate pure-Python auditor exactly reconstructed the candidate's gates for all 4,096 subsets. All four preregistered mutation controls were rejected.

In the intentionally misleading full synthetic ledger, 10/12 rows are qualified PASS (83.33%), above the flat 80% threshold, and every factor level has at least one qualified PASS. The certificate nevertheless refuses the wide applicability claim: one feasible predecessor is a known FAIL, one effect-positive row is UNKNOWN because its route is not independently qualified, and these states contaminate required pair projections. The exact `t01` narrow claim remains supported by its direct qualified PASS. Across the 4,096 possible retained-evidence subsets, 1,987 produce a simultaneous flat-count/factorwise wide promotion that the certificate refuses. This count is over constructed evidence subsets, not empirical skill trials.

## Reproduction and raw evidence

- Frozen source/input and H/T/D/C/U: [`FREEZE.md`](FREEZE.md).
- Exact synthetic fixture: [`FIXTURE.json`](FIXTURE.json).
- CUDA candidate and raw result: [`candidate.py`](candidate.py), [`CANDIDATE_RAW.json`](RAW_EVIDENCE.zip).
- Independent CPU auditor and raw audit: [`auditor.py`](auditor.py), [`AUDIT_RAW.json`](RAW_EVIDENCE.zip).
- Construction checks: [`test_construction.py`](test_construction.py); 5/5 passed before freeze. Both Python files passed `py_compile`.
- Candidate invocation: one, exit 0; auditor invocation: one, exit 0; formal retries and reruns: zero.
- Device: NVIDIA GeForce RTX 3080 Laptop GPU; CUDA runtime 12.1; PyTorch 2.5.1+cu121; Python 3.11.9.
- SHA-256 identities: [`SHA256SUMS.txt`](SHA256SUMS.txt). Run metadata and exact commands: [`RUN_RECORD.json`](RUN_RECORD.json).

Docker was not used. The Windows Docker service was stopped; the active Arch WSL distro had no Docker Desktop integration, Podman, or nerdctl. The `docker-desktop` WSL distro showed Running, so it and any shared workloads were left untouched. The fixture had no network, GUI, model, application, physical-input, or external effects. The local GPU path was explicitly exercised; no GPU-vs-CPU speed or necessity claim is made.

## Scope and limits

This validates only a finite certificate method against a constructed truth fixture. The infeasible dialog/alternate combination is stipulated, not validated against a real skill. The result does not establish any real reusable skill's applicability, GUI correctness, authority, safety, broad coverage, or product benefit. Pairwise coverage does not prove absence of higher-order or history-sensitive faults. A simple per-condition ledger may be sufficient; further certificate complexity is not justified by this T0 alone. No historical result is modified and no live skill is promoted.
