# Issue #6556 T0 — post-retirement cue commission challenge

## Result

Status: **`METHOD_PASS_SCOPED`** for this finite synthetic protocol only. The independent raw-only auditor reconstructed all 50/50 case-policy rows, reported zero errors, no origin-fence unsafe admission, no origin-fence eligible miss, and preserved all 50 obligation states without falsely resolving an effect or release.

| Policy | Oracle-ineligible admissions | Eligible misses | Misattributed admissions |
|---|---:|---:|---:|
| Cue-only | 6 | 0 | 5 |
| Unsubscribe-only | 6 | 0 | 5 |
| Current generation at delivery | 6 | 0 | 5 |
| Durable instance + event ID | 2 | 0 | 2 |
| Origin-generation retirement fence | 0 | 0 | 0 |

The origin-fence returned `UNKNOWN` in both histories where origin provenance was absent: an old event rebound to B and a restart with both origin and retirement receipt missing. In the stipulated fresh-B and still-active-A histories it admitted the correct lineage. This does not establish any of these policies' behavior in a deployed watcher.

The durable instance/event-ID comparator refused the old event delivered to a B listener but still targeted at retired A, and it admitted fresh B. It also admitted the two synthetic provenance-loss/rebinding histories as B, which is why the origin-bound fence changes the result in this particular matrix. This is not evidence that production routing loses provenance, nor evidence that an additional durable receipt is worth its cost when routing is preserved.

## Execution provenance

- Native Microsoft WSL Containers, `C:\Program Files\WSL\wslc.exe`, reported `wslc 3.0.1.0`.
- Cached image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; no pull, network disabled, 1 CPU, requested memory 1 GiB, UID 65534.
- Construction, candidate, and auditor each ran exactly once in separate WSLc containers. Construction tests: 12/12. Candidate and auditor both exited 0.
- Candidate received only `candidate_source/` (candidate + fixture); auditor received read-only `audit_source/` (auditor + fixture + oracle) and byte-identical raw candidate output. Candidate raw SHA-256: `e87198564ea9ba9fd4660ebe5673c858f347012ec464d74c171f5268b4f8d3e3`; audit copy matched.
- No Docker, Podman, GPU, GUI, network access, live service, model, or user data was used.
- WSLc emitted verbatim: `wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` Therefore the configured memory cap is **not claimed as enforced**.

Commands, timestamps, exit codes, raw stdout/stderr, audit JSON, and candidate bytes are retained in this directory's stage folders. `FREEZE.json` contains the frozen source hashes and preregistration main SHA. The candidate source and auditor source were isolated in separate read-only mounts.

## Construction / decision limits

The experiment tests a deterministic policy simulator against a stipulated independent oracle. It does not model actual queue ordering, atomic retirement, intent-revision scheduling, operating-system event delivery, durable-store crash semantics, concurrent watcher processes, external effect execution, or release completion. Specifically, explicit intent-revision scheduling and a cue queued before retirement but delivered afterward are outside this T0. The 50 rows are not statistical trials. No prevalence, runtime safety/reliability, human prospective-memory transfer, latency, or product benefit is inferred. Follow-up empirical work requires a real, authorized watcher/event source and must not reuse this consumed allocation.
