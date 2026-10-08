# Allocation-03 exact execution record

Disposition: `PASS_METHOD_SCOPED` for the finite synthetic clock/owner fixture only. Allocations 01 and 02 stopped before any container/candidate/auditor invocation because `origin/main` advanced after each preregistration; their STOP records are retained at `../formal-01/STOP.json` and `../formal-02/STOP.json`. No experiment was consumed or retried. Allocation-03 is the first executed candidate.

## Frozen identity and gates

- Source base/main at prelaunch: `c09f073f2a6e078c0fe5d8192246cc821cecc29c`.
- Exact current runtime Lease: `research/live_control/lease.py`, SHA-256 `e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f`.
- Image `python:3.12-slim`, ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, Linux/arm64; OrbStack Docker 29.4.0 / Linux aarch64.
- Candidate SHA-256 `0f5581000cb3d8a5f9c206bdd34ae18d6e5c8c89f31ac4e07c00566f93446ca3`; auditor SHA-256 `8ea0402073fa78564570dbb343323bcdce0bf2b7dd6c468851e848bbebcf92e4`; fixture SHA-256 `27a43156adc712307253133305e1c600d5e72919aecd315419d1c68db44466bd`.
- Construction checks: 4/4 pass before and after main fast-forward; they are not the formal outcome.

## Candidate command

```sh
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges \
  --mount type=bind,src="$PWD/research/live_control/lease.py",dst=/src/lease.py,readonly \
  --mount type=bind,src="$PWD/research/analysis/wake_fence_6331_t0_v1/candidate.py",dst=/src/candidate.py,readonly \
  --mount type=bind,src="$PWD/research/analysis/wake_fence_6331_t0_v1/fixture.json",dst=/src/fixture.json,readonly \
  --mount type=bind,src="$PWD/research/analysis/wake_fence_6331_t0_v1/results/formal-03",dst=/out \
  --workdir /out --entrypoint python python:3.12-slim \
  /src/candidate.py /src/fixture.json /out/candidate.raw.json
```

Invocations 1, exit 0, stdout 0 bytes, stderr 0 bytes, candidate raw 6,217 bytes. Candidate had no auditor source or expected verdict table.

## Independent auditor command

```sh
docker run --rm --pull=never --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges \
  --mount type=bind,src="$PWD/research/analysis/wake_fence_6331_t0_v1/audit.py",dst=/src/audit.py,readonly \
  --mount type=bind,src="$PWD/research/analysis/wake_fence_6331_t0_v1/fixture.json",dst=/src/fixture.json,readonly \
  --mount type=bind,src="$PWD/research/analysis/wake_fence_6331_t0_v1/results/formal-03/candidate.raw.json",dst=/src/candidate.raw.json,readonly \
  --mount type=bind,src="$PWD/research/analysis/wake_fence_6331_t0_v1/results/formal-03",dst=/out \
  --workdir /out --entrypoint python python:3.12-slim \
  /src/audit.py /src/fixture.json /src/candidate.raw.json /out/audit.raw.json
```

Invocations 1, exit 0, stdout 0 bytes, stderr 0 bytes, audit raw 2,296 bytes. Auditor received no candidate source or imported runtime Lease.

## Result and interpretation

Auditor reconstructed all 24 arm/scenario rows in exact order; all four corruption controls rejected. Under the long-wake synthetic trace the exact current perf-counter Lease returns LIVE while the BOOTTIME deadline returns EXPIRED; the wake fence returns `BLOCK_STALE_GENERATION`. No-gap control admits under current lease. Exact awake deadline (`now == deadline`) is EXPIRED, matching current `Lease.check()` semantics. Missing/late wake notice returns `UNKNOWN_WAKE_COVERAGE` and suppresses the first action. If an input-held marker is present, the fence emits a release request; it asserts release only when the synthetic trace separately carries acknowledgement. A fresh authority is admitted only for the explicit ack+rebind trace.

The result supports only this finite synthetic model and source contract. It does not demonstrate host suspend behavior, OrbStack/WSLc clock mapping, actual wake-event delivery, real release, GUI focus/source revalidation, task outcome, or production safety. No actual machine sleep, GUI, model, or physical input occurred.
