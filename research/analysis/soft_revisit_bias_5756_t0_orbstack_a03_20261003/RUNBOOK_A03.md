# Allocation A03 — OrbStack runbook

The A01 and A02 source/hash STOP records remain unchanged. This is a fresh allocation using the exact source hashes pinned in `FREEZE.json`; it is not a retry. Current `main` must still be `fa791fe937fb24245e785d9e22928b3f4a6a42ae` immediately before each stage. Confirm the pinned image remains present at the exact digest/platform, the dedicated output mount is empty, and the OrbStack container inventory has no run for this allocation. Do not inspect, stop, or modify other owners' machines or containers. This bounded deterministic workload does not measure latency and has a 0.25 CPU limit.

Frozen locations:

- Source: `research/analysis/soft_revisit_bias_5756_t0_wslc_20261002/` (read-only; 9 source hashes are listed in `FREEZE.json`).
- Output: this allocation's `candidate/` and `audit/` directories; they are separate from source and each other.
- Image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, platform `linux/arm64`, already cached.
- All containers use `--pull never --network none --platform linux/arm64 --cpus 0.25 --memory 512m --user 65534:65534`.

## Construction — one invocation

```sh
docker --context orbstack run --rm --pull never --platform linux/arm64 --network none --cpus 0.25 --memory 512m --user 65534:65534 \
  --mount type=bind,source="$SOURCE",target=/src,readonly --workdir /src \
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python -B run_construction.py
```

The source runner requires `/sys/fs/cgroup/memory.max` to equal 536870912 before it starts the 13 tests. Preserve stdout/stderr and exit code. On any mismatch or failure, stop this allocation before candidate execution; no retry.

## Candidate — one invocation, only after construction passes

```sh
docker --context orbstack run --rm --pull never --platform linux/arm64 --network none --cpus 0.25 --memory 512m --user 65534:65534 \
  --mount type=bind,source="$SOURCE",target=/src,readonly \
  --mount type=bind,source="$CANDIDATE_OUT",target=/out \
  --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python -B run_candidate.py --output /out/raw.jsonl
```

`CANDIDATE_OUT` must be fresh and empty. Preserve the first bytes/status even if the process outcome is ambiguous; do not rerun.

## Independent raw-only audit — one invocation only after candidate exit 0

```sh
docker --context orbstack run --rm --pull never --platform linux/arm64 --network none --cpus 0.25 --memory 512m --user 65534:65534 \
  --mount type=bind,source="$SOURCE",target=/src,readonly \
  --mount type=bind,source="$CANDIDATE_OUT",target=/in,readonly \
  --mount type=bind,source="$AUDIT_OUT",target=/out \
  --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python -B run_audit.py --input /in/raw.jsonl --output /out/audit.json
```

`AUDIT_OUT` must be distinct, fresh and empty. The auditor is a separate process and reads candidate raw only; it reconstructs the fixture/oracle and emits all four policy results and three contrasts. Construction=1, candidate<=1, auditor<=1, retries=0.
