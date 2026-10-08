# A09 container infrastructure STOP

- Issue: [#5309](https://github.com/Unjuno/agent-interface/issues/5309)
- Allocation: `5309-WITNESS-A09-ORBSTACK-20261007`
- Status: `STOP_ENGINE_CONTENT_BLOB_UNREADABLE`
- Date: 2026-10-07 (Asia/Tokyo)
- Base main observed: `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`
- Branch: `research/5309-witness-heldout-a09-20261007`

## H/T/D/C/U (planned, not executed)

- **H:** On held-out, non-isomorphic finite transition families, a witness-aware chooser constrained by an explicit preservation-cost budget yields a larger fraction of independently verified completion than generic information gain only when the preservation prediction is correct and cost is within budget; it must yield UNKNOWN when the model is contradicted or every preserving action exceeds budget.
- **T:** Deterministic exhaustive finite state families with cycle, branch/merge, and asymmetric transition topologies; paired equal-admissibility actions; vary witness prediction correctness and preservation cost below/at/above a fixed budget. Candidate sees only observations/predictions; independent auditor alone sees transition truth. No GUI, model, network, or authority.
- **D:** Planned PASS requires an independent raw-only audit over every frozen row, same action sets, correct completion only with an observed independent effect witness, no false completion under prediction error or over-budget cost, and exact comparison against generic IG. This gate was never run.
- **C:** These remain authored finite simulators; ranking advantage can disappear with mandatory readback or an existing witness; cost/budget units are arbitrary and not calibrated.
- **U:** No result about natural GUI dynamics, frequency, runtime, safety, user performance, or product benefit.

## Observed STOP evidence

OrbStack Docker Engine reports version 29.4.0. Before creating any A09 container, `docker image inspect python:3.12-slim` failed with `rpc error: code = Unknown desc = blob sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f ... operation not supported`. A fresh `docker pull --platform linux/arm64 python:3.12-slim` failed with the same content-store error. A read-only inventory attempt (`docker image ls --digests`) then failed on another missing/unreadable blob. `docker ps -a --no-trunc` indicated a large pre-existing inventory (100 container IDs); therefore no prune, repair, deletion, or container modification was attempted.

Formal candidate invocations: 0. Auditor invocations: 0. Candidate raw: absent. Audit: absent. Scientific outcome: none. Retries of the Docker operations: none; the one inspect, one pull, and one inventory probe are preserved as distinct infrastructure observations. A09 did not run and does not test or refute its H.

## Restart gate

Do not rerun this allocation. A separately frozen successor may proceed only after an operator verifies OrbStack content-store health and safely identifies the owned execution environment, then confirms pinned image digest, isolated mounts, and no conflicting allocation. Preserve all existing Docker data and containers. If the same host error recurs, keep it as an infrastructure STOP; do not switch engines or claim a scientific result under this allocation.
