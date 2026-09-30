# Issue #5531 T4 — hierarchical common-cause boundary

## H/T/D/C/U

- **H:** Under a declared site-level fault model, counting different observer, host, or rack names can overstate independent crash evidence. Aggregating by the configured site prevents same-site reports from crossing the toy terminal-failure threshold; two current reports from distinct sites still cross it.
- **T:** Five frozen synthetic records, generation 7, site-level cut (`domain_path[0]`), threshold 2. Candidate ran once in a network-disabled, read-only Docker container. A second container ran the independent literal-table auditor with only `audit.py` and `candidate.json` mounted.
- **D:** Scoped PASS: all five classifications and counts matched the frozen oracle; independent audit returned `PASS`, `errors=[]`; both containers exited 0. Seven local construction tests passed, including rejection of a same-site `FAILED` mutation.
- **C:** If configured site groups are not meaningful failure domains, aggregation can hide genuinely independent observers or produce false suspicion. Correctly typed failure-domain witnesses may already suffice without a new reducer.
- **U:** The topology is synthetic and supplied by the fixture. Shared global/cloud control planes, network partitions, domain discovery, real failure timing, probabilities, detector completeness/accuracy in deployment, authority, GUI behavior, and production availability were not tested. This does not establish that false revocations are reduced in real systems.

## Frozen cases and results

| Case | Independent domains / valid observers | Result |
|---|---:|---|
| Two hosts, same rack and site | 1 / 2 | `SUSPECTED_UNAVAILABLE` |
| Different racks, same site | 1 / 2 | `SUSPECTED_UNAVAILABLE` |
| Two current witnesses, different sites | 2 / 2 | `FAILED` |
| Second-site witness has stale generation | 1 / 1 | `SUSPECTED_UNAVAILABLE` |
| One observer claims two sites; other valid observer is in site A | 1 / 1 | `SUSPECTED_UNAVAILABLE` |

The depth-1 cut deliberately treats a site as one failure domain and excludes common infrastructure above sites from the model. `FAILED` here is only the simulator's typed classification; the runner grants no effect authority.

## Execution evidence

- Base main frozen at `59ffec5d551b0adcf11057eee6da814237a748c8`.
- Docker Engine `28.5.1`, Linux `x86_64`; `python:3.12-slim` image ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
- A separate read-only bind preflight read 2,024 bytes of `cases.json`; its SHA-256 matched the frozen `03d19c53f2cb9e7c924d2dba4d110628ee3933e5eb19a2d5c93adda651a3cd7a`.
- Candidate container: `liveness-5531-t4-candidate-20261001`, exit 0, read-only root, network `none`, 256 MiB, 1 CPU, all capabilities dropped, `no-new-privileges`; only cases, detector, and runner were mounted read-only. Exact stdout is [`candidate.json`](candidate.json).
- Auditor container: `liveness-5531-t4-auditor-20261001`, exit 0 with the same isolation; only `audit.py` and the raw candidate JSON were mounted read-only (candidate implementation and input cases were not mounted). Exact stdout is [`audit.json`](audit.json).
- The construction/mutation suite: `python -B -m unittest -v`, 7 passed. The formal candidate was not rerun.

See [`PLAN.md`](PLAN.md), [`FREEZE.json`](FREEZE.json), and [`execution.json`](execution.json) for the preregistration and exact container command/configuration record.

[`SHA256SUMS.txt`](SHA256SUMS.txt) binds all 11 source, input, candidate, audit, and report artifacts to their exact bytes.

## Parallel-work coordination

After this one-shot run, Issue #5531 received a separate delay-correlation T4 allocation, retained as STOP and integrated by PR #5559. This package tests the distinct site-level witness-aggregation boundary (`T4-HIER-01`); it does not alter, repair, or retry that timing allocation. The two result paths and frozen inputs are separate. Future Issue #5531 rung references should use the unique allocation suffix to avoid ordinal ambiguity.
