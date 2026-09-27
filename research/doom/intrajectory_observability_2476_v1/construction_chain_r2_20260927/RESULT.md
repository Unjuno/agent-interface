# Result — cumulative track-drift construction r2

Allocation: `issue2476-track-cumulative-drift-construction-r2-20260927`
Disposition: **`FAIL_CUMULATIVE_DRIFT_GATE`** (independent evidence-completeness audit failed).

## Executed locally

Both commands used the locally cached image ID from `ENVIRONMENT.json`; the
source was mounted read-only and the dedicated `output/` directory was the
only writable mount. The auditor ran once, after the runner, in a separate
container. No GitHub Actions workflow executed the experiment.

```text
docker run --rm --pull=never --platform=linux/amd64 --network=none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m --cpus=1 --memory=268435456 \
  --memory-swap=268435456 --pids-limit=32 --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --mount type=bind,source=<frozen-source>,target=/source,readonly \
  --mount type=bind,source=<dedicated-output>,target=/out \
  --workdir=/source --entrypoint=python python:3.13.5-slim-bookworm \
  -B /source/run.py --source /source --out /out

docker run --rm --pull=never --platform=linux/amd64 --network=none --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m --cpus=1 --memory=268435456 \
  --memory-swap=268435456 --pids-limit=32 --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --mount type=bind,source=<frozen-source>,target=/source,readonly \
  --mount type=bind,source=<dedicated-output>,target=/out \
  --workdir=/source --entrypoint=python python:3.13.5-slim-bookworm \
  -B /source/audit.py --source /source --out /out
```

The actual local workspace path is intentionally omitted from this public
record. The frozen source directory was mounted read-only at `/source`; its
dedicated `output` child was mounted writable at `/out`. Image identity was
checked before start: `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`.

Runner exit: 0; 10 cases produced. Independent auditor exit: 1; 20 policy rows
examined; final audit decision `FAIL_CUMULATIVE_DRIFT_GATE` with nine
`INPUT_EMITTED` errors. Raw trace SHA-256:
`0075f4be9bafa24836ba1c49f704ce3c3cd0fe9092e0346e14a6c1e4ed4b88d6`.
Raw audit SHA-256:
`3e30e94f8cb29ae66ce482b6f1bc686d4c7b9be85b73480c111009cc7aabb5ed`.

## What the raw trace contains

The exact three-hop and exactly-12-px cumulative cases tracked all three hops
under both policies. In the repeated 8-px per-hop-residual case, the
per-hop-only comparator tracked all three while the global-cap policy stopped
at hop 2 with 16 px global drift. In the 4+4+5 case, the global-cap policy
stopped at hop 3 when drift reached 13 px. The abrupt-translation, target-loss,
low-score, stale-age, geometry-change and sequence-gap controls stopped at the
declared step. These are observations in the retained raw trace, **not a PASS**:
the independent audit did not accept the complete evidence bundle.

## Why the gate failed

When a policy stopped, `run.py` represented later scheduled hops as
`NOT_REACHED_AFTER_STOP` but omitted the required per-hop
`physical_input_emitted: false` field. The audit therefore correctly rejected
the missing evidence in nine skipped rows, despite the runner's top-level
`physical_input_emissions: 0` and explicit false values for reached steps. The
freeze required row-level independent reconciliation, so this is an evidence
integrity failure, not an audit warning to waive. No frozen source, trace, or
audit was edited; no retry or repair occurred.

Physical input emissions: 0. GUI/game/model/provider/network: none. Formal
Issue #2476 trajectory cases: 0. This synthetic construction does not validate
real image matching, target identity, task effect, or trajectory improvement.
