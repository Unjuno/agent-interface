# Allocation 02 WSLc runbook

Use the exact source path under `research/analysis/soft_revisit_bias_5756_t0_wslc_20261002`. Do not use Docker Desktop or Podman; the requested runtime is Microsoft WSLc/native WSL containers. This is a CPU-only finite synthetic comparison, so the GPU is intentionally unused.

## Start gate

Immediately before any container, verify: (1) GitHub main still equals `FREEZE_A2.json.base_main_sha`; (2) all frozen file hashes match; (3) the cached image digest exists (`wslc images`) and no pull/build is needed; (4) exact output path is fresh; (5) the WSLc owner of Issue #6477 or repository owner explicitly released the shared lane. An empty `wslc container list`, zero GPU utilization, or elapsed wall time is not a release.

If the source/main or ownership gate fails, retain STOP with candidate=0 and auditor=0. Do not consume a container run.

## Construction (one allocation-02 invocation)

```powershell
wslc run --rm --name soft-revisit-5756-a2-construction --pull never --network none --cpus 0.25 --memory 512M --user 65534:65534 --volume "<absolute-experiment-path>:/src:ro" --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B run_construction.py
```

The wrapper prints `/sys/fs/cgroup/memory.max` and requires exactly 536870912 bytes before it runs the 13-test construction suite. Save exact stdout/stderr, WSLc `inspect` timestamps and ID, exit code, image ID/digest, and any warnings. If the cgroup value differs or is `max`, stop before the tests and preserve the failure; do not retry this allocation.

## Formal candidate (one invocation)

Only after construction exits 0 and all gates remain valid, mount the source read-only and a new empty output directory read-write:

```powershell
wslc run --rm --name soft-revisit-5756-a2-candidate --pull never --network none --cpus 0.25 --memory 512M --user 65534:65534 --volume "<absolute-experiment-path>:/src:ro" --volume "<fresh-candidate-output-path>:/out:rw" --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B run_candidate.py --output /out/raw.jsonl
```

If result status is ambiguous, inspect the same container and preserve all bytes; do not invoke candidate again.

## Independent raw-only audit (one invocation, only if candidate exits 0)

Use a new container; mount frozen source and candidate output read-only, plus a distinct empty audit directory read-write:

```powershell
wslc run --rm --name soft-revisit-5756-a2-audit --pull never --network none --cpus 0.25 --memory 512M --user 65534:65534 --volume "<absolute-experiment-path>:/src:ro" --volume "<candidate-output-path>:/in:ro" --volume "<fresh-audit-output-path>:/out:rw" --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B run_audit.py --input /in/raw.jsonl --output /out/audit.json
```

One candidate and one auditor max; no retries. Retain raw outputs, exact runtime records and SHA-256 before reporting. The all-policy table must show soft, hard, stateless and exhaustive; if soft ties stateless, state explicitly that this does not support a soft-specific advantage. This finite authored fixture does not establish live GUI transfer, real-world performance, or safety guarantees.
