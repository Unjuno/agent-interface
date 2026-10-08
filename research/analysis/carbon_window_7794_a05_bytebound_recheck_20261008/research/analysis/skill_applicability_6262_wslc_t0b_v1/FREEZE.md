# Issue #6262 — WSL Podman CUDA environment successor freeze

Experiment: `AI-6262-T0B-WSLC-GPU-20261002-01`  
Freeze time: 2026-10-02 08:42 JST, before candidate invocation  
Successor source commit: `8b154b1f0ebb35dc7faa2eb4929cda9e35193604` (PR #6289 head)

## H / T / D / C / U

**H.** The exact frozen #6262 synthetic candidate and fixture will enumerate all 4,096 evidence subsets under a pinned PyTorch/CUDA image in a WSL Podman container with NVIDIA CDI passthrough. A separate standard-library auditor will reproduce every semantic output field and reject all four frozen corruption controls. A mismatch or unavailable GPU is `STOP` and will not be retried.

**T0B.** This is a new, separately identified environment-reproduction allocation, not a retry or edit of `AI-6262-T0-GPU-20261002-01`. Mount the original candidate/fixture/auditor read-only; mount a new, separate output directory read-write; disable container networking; expose only `nvidia.com/gpu=all` to the candidate. Run candidate exactly once and independent auditor exactly once. Auditor gets the exact fixture bytes copied into the output mount and audits the candidate raw output without importing candidate code. No source, fixture, decision, or predecessor result changes.

**D.** `PASS_CONTAINER_REPRODUCTION_SCOPED` only if candidate exits 0, reports CUDA available with `NVIDIA GeForce RTX 3080 Laptop GPU`, hashes the exact fixture, and enumerates 4,096 subsets / 12 feasible cells / 23 pair projections; auditor exits 0, exactly matches semantic fields, reconstructs all 4,096 rows, refuses the wide claim, retains the exact qualified `t01` claim, and rejects all 4/4 frozen mutations. Any mismatch or infrastructure failure is retained as `FAIL`/`STOP`; no candidate retry or source repair.

**C.** This checks runtime portability and local GPU-container access only. The finite method fixture could run on CPU; GPU use is not necessary and no speedup is predicted.

**U.** Synthetic method fixture only: no retained skill, GUI, model, user task, safety, or product claim. It does not establish general Podman/Docker parity or resource-limit enforcement. Container networking is disabled for both invocations. GPU/model output is not authoritative over the independent CPU audit.

## Frozen inputs and execution environment

Original fixture SHA-256: `adc342e1416ed13d1cd38a9e881cf1b5163548a8ce83f02670ffef3f91964715`  
Candidate SHA-256: `2dfdcd061e845f7bbf9e68aba72e2675a2c8b2cf91f62b81bca876b1b568f157`  
Auditor SHA-256: `f9aa23b1da71051ea1fd83dbc374234782e837856b0e99c0ba4c025f4aa5c901`

Arch Linux WSL2, kernel `6.18.40.1-microsoft-standard-WSL2`; Podman `6.1.3`; cgroup v2; NVIDIA driver `581.57`; RTX 3080 Laptop GPU, 16 GiB. Image: `docker.io/pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`, linux/amd64, PyTorch `2.5.1+cu121`, CUDA runtime `12.1`. Image pull was completed before freeze. Preflight GPU smoke test passed (CUDA available and correct device); candidate and auditor have not yet run for this allocation.

## Frozen commands

Candidate (one formal invocation):

```bash
podman run --rm --network none --device nvidia.com/gpu=all \
  --volume /home/unjuno/agent-interface-6289-review/research/analysis/skill_applicability_6262_gpu_t0_v1:/src:ro \
  --volume /home/unjuno/research_6262_wslc_gpu_successor:/out:rw \
  --workdir /src \
  docker.io/pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067 \
  python /src/candidate.py /out/CANDIDATE_RAW.json
```

Before audit, copy `/src/FIXTURE.json` byte-for-byte to `/out/FIXTURE.json`; verify its SHA-256 against the frozen value above. Auditor (one formal invocation; CPU only):

```bash
podman run --rm --network none \
  --volume /home/unjuno/agent-interface-6289-review/research/analysis/skill_applicability_6262_gpu_t0_v1:/src:ro \
  --volume /home/unjuno/research_6262_wslc_gpu_successor:/out:rw \
  --workdir /out \
  docker.io/pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067 \
  python /src/auditor.py /out/FIXTURE.json /out/CANDIDATE_RAW.json
```

No container, candidate, or auditor invocation has yet been made for this frozen allocation. The separate CUDA runtime smoke test and an earlier pre-freeze invalid-image-ID probe are construction/environment checks, not candidate attempts.

