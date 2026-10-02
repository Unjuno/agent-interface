# OrbStack allocation 03 — Issue #6350 finite audit successor

Status at freeze: `PREREGISTERED_NOT_RUN`.

## Why this allocation exists

The Issue's allocation `...-02` had a requested WSLc time window that elapsed without an explicit coordinator grant. It remains unconsumed and unchanged. The user has now directly asked this task to execute the Issue idea in a Docker/OrbStack container and retain the result in `main`. Allocation 03 is a fresh, one-shot CPU container allocation under the same scientific Issue, not a reuse of the expired window and not a new scientific hypothesis.

## H / T / D / C / U

**H:** The corrected finite renderer will distinguish current-generation `VERIFIED`, `NOT_APPLIED_VERIFIED`, `UNKNOWN`, and stale-generation-as-`UNKNOWN`, preserve task-terminal status as a separate conjunction, reconstruct the exact predecessor fixture, and reject all four frozen semantic mutations.

**T:** Allocation `EFFECT-TERMINAL-FEEDBACK-6301-T0-ORB-20261002-03`. Frozen current main after additive parallel commits: `762bb46b5037a2cd4a09672a2e130760a96ff669`. Candidate package commit: `43e921435` (six additive files); fixture origin remains `eba652642a7a741d57bbdfe0c1a9929d3b15bd7f`. The eight-test host construction suite passed before this freeze. Exact SHA-256 values are in `FREEZE.json`; fixture/candidate/auditor/test hashes are respectively `35bfa13d5edee93d834ddc54c980bb24a48b8a5bb9a4e9bcc9dcddd11d1b51a9`, `b41036c61ebece89a2f1b990e7ae2f9b896512fc2983b29a9b4dd9e712c9cc88`, `831ad1e7a499b1d28bd5b0b9fbfb10b9f5409eddc47460e4a28209d84055977e`, and `5e206a9109b4c4442c3ba52facd14559c8241b339c8fbf648575da4377a7542a`.

Run construction tests once in a fresh network-disabled container. Only on success, run candidate once in its own network-disabled container, then the independent raw-only auditor once in a separate container only if candidate exits 0. Container engine: dedicated OrbStack Ubuntu 24.04 ARM64 VM `effect-terminal-feedback-6301-t0-orbstack-20261002`, Docker Engine 29.1.3. Container image was exported from the host's pre-existing cache and imported without a pull. The source cache identifies it as `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; the imported engine retains immutable image ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` but no RepoDigest alias, so execution is pinned by image ID. Record interpreter version in the first construction container. Each formal container uses read-only rootfs, network none, requested 0.25 CPU / 512 MiB / 64 PIDs, UID/GID 65534, read-only source/fixture, and a unique fresh writable output directory. Construction=1, candidate<=1, auditor<=1, retries=0. No model, GUI, game, GPU, user input/data, or external task effects.

The ARM64 OrbStack runtime differs from the expired WSLc proposal's linux/amd64 environment. This finite test compares deterministic semantics, not speed; no cross-architecture/runtime performance inference is permitted. Any infrastructure, identity, mount, or source mismatch is a retained STOP without retry.

Exact container commands are frozen in `run_orbstack.sh` (committed before any container invocation); its immutable image argument is the imported image ID above. Output paths must be absent at the start gate. The script executes only the requested single stage and refuses to run a later stage unless prior exit/result gates pass.

**D:** `PASS_METHOD_SCOPED` only if the raw-only auditor reconstructs all 10 task rows and 30 display records from the frozen fixture, all four mutations reject, the stale receipt remains UNKNOWN, verified non-application is not described as unknown, accepted input is not promoted to effect, and task terminal remains PENDING where obligations remain. Any mismatch is FAIL/STOP; missing/altered artifacts or a container/mount issue is STOP. No retry.

**C:** Synthetic deterministic truth table only. No model response, live GUI effect, user-visible benefit, latency, safety rate, MAP01 behavior, or product result is measured.

**U:** Behavior across Python versions/architectures, live model cue interpretation, real application effect, user task success, generality beyond the fixture, and any production safety/efficiency benefit.

## Preformal notes

- Construction suite on host CPython: 8/8 passed; formal counters still 0/0/0.
- Shared OrbStack Docker inventory contained active work, so no commands will be sent to the shared engine. This allocation uses a newly created dedicated OrbStack VM and its own Docker daemon.
- The VM's requested CPU/memory configuration is not itself proof of cgroup enforcement; inspect and retain Docker's effective cgroup/resource reports. No hard resource-enforcement claim without observed support.
