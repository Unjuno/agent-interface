# Needle pilot-05 — in-envelope near-boundary shift

Issue: https://github.com/Unjuno/agent-interface/issues/3847  
Allocation: `needle-intent-distill-3458-pilot-05-near-boundary-shift`

This successor tests whether pilot-04's fixed hybrid selective Needle remains useful when in-envelope CORRECT states move toward (but remain outside) the known deterministic YIELD margin. Full preregistration and frozen gates are in `PREREGISTRATION.md`. Previous pilot results are unchanged.

## Reproduction

Build only from the already cached `python:3.12-slim-bookworm` base; this build installs CPU PyTorch 2.5.1. Do not pull a base image or prune Docker caches. Run construction checks in the built image before freezing. The formal runner is one-shot and writes complete lossless row-level evidence to a new, empty output directory:

```powershell
docker build --pull=false -f research/system1/needle_distill_3458_pilot_05_near_boundary_shift/Dockerfile -t needle-pilot05:local .
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=256m -v ${PWD}/research/system1/needle_distill_3458_pilot_05_near_boundary_shift:/src:ro -v ${PWD}/research/system1/needle_distill_3458_pilot_05_near_boundary_shift/formal:/out needle-pilot05:local /src/runner.py --out /out/formal-01
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=128m -v ${PWD}/research/system1/needle_distill_3458_pilot_05_near_boundary_shift:/src:ro -v ${PWD}/research/system1/needle_distill_3458_pilot_05_near_boundary_shift/formal:/evidence:ro -v ${PWD}/research/system1/needle_distill_3458_pilot_05_near_boundary_shift/audit:/out needle-pilot05:local /src/audit.py /evidence/formal-01/FORMAL_RESULT.json --out /out/AUDIT.json
```

The image build has network access solely to install the pinned dependency; both executions are `--network none`. Bind mounts are read-only except dedicated result/audit directories. Construction tests do not train. Formal output is never redirected through a shell capture buffer. Do not rerun a failed or truncated formal allocation.

## Evidence

`FREEZE.json`, `FORMAL_RESULT.json`, `AUDIT.json`, `SHA256SUMS`, exact runner/auditor/tests, environment record and `REPORT.md` preserve the allocation. The independent auditor recomputes every teacher label, accepted proposal, per-class metric, yield reason, boundary result and latency percentile from retained raw rows/samples without importing the runner.

## Limits

Even a PASS is limited to one synthetic teacher and three seeds. It is not external/Astra intent fidelity, perception, GUI control, action effect, real-time system evidence, execution authority or product readiness.
