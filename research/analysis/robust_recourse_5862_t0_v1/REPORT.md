# Issue #5862 — belief-robust recourse T0 report

## Result

**METHOD_PASS_SCOPED**, limited to the preregistered seven-case synthetic transition model. GitHub Actions run [36828007341](https://github.com/Unjuno/agent-interface/actions/runs/36828007341) ran the candidate once and the independent auditor once in separate Docker containers; both exited 0 and the auditor reconstructed all seven case dispositions and accepted all six mutation controls.

| Disposition | Cases |
|---|---:|
| `ROBUST_ADVISORY` | 4 |
| `CONDITIONAL_ADVISORY` | 2 |
| `NO_ROUTE_WITHIN_BOUND` | 1 |

The uncertain-delivery case contains two worlds with exactly the same typed `BLOCKED` receipt: delivery uncommitted versus an irreversible effect already committed. Generic retry is not robust across that belief, although it has a single-world existential witness; the candidate instead selects `inspect_then_branch`, a shared safe first action followed by observation-conditioned retry or reconciliation. This is a finite-model counterexample to treating an existential path as actionable robust advice, not evidence that any live task was recovered.

The four robust routes are `reacquire_then_act`, `refresh_then_act`, `inspect_then_branch`, and `inspect_then_reconcile`. Revoked authority and human takeover remain explicitly conditional. The genuinely absent target is only `NO_ROUTE_WITHIN_BOUND`; this does not claim global impossibility. No case emitted authority or executable coordinates.

## Execution evidence

Allocation `5862-ROBUST-RECOURSE-T0-20261001-01`, workflow run number 1 / attempt 1, frozen event SHA `dec0c356cafeb0a3c75ae0c5172b019277a3c3d5`. GitHub-hosted runner Docker Engine was 28.0.4. Separate linux/amd64 containers used `python:3.12.14-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, network none, read-only root, 128 MiB, 1 CPU, pids 32, cap-drop ALL, and no-new-privileges; both exited 0 with OOM false. The raw candidate output SHA256 is `7a14c8550ddb26684436d958762eb4f0bc118495610f07eaa8e29263b09a8777`, recorded in `SHA256SUMS`.

Raw candidate output, independent audit summary, Docker server/image identity, both container inspections and start-gate record are retained under `results/5862-ROBUST-RECOURSE-T0-20261001-01/`.

## Limits and next step

This establishes only that this candidate and auditor agree on this frozen, hand-authored finite abstraction. It does not establish state/transition completeness, live effect observation, integration with a real agent-interface, human comprehension, safety in production, or successful real-world recovery. Keep #5862 open for a source-bound real stop-receipt/effect oracle study; preserve this T0 outcome unchanged. Any follow-up must represent hidden worlds and adverse effects explicitly and may not relabel bounded no-route as global impossibility.
