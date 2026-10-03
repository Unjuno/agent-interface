# Issue #6354 A02 — WSLc construction validation

## H / T / D / C / U

- **H:** The additive A02 role-conflict probe builder and independent raw auditor reproduce the corrected contradictory-label probe contract in the requested native WSL container runtime.
- **T:** Using unchanged candidate, auditor, tests, and frozen allocation-01 dataset from `needle_role_conflict_probe_6354_a02`, run the 8-test construction suite, then one candidate invocation and—only after candidate exit 0—one separate raw-only auditor invocation. All containers use cached pinned Python image, network disabled, read-only source, 0.25 CPU, 512 MiB memory, UID/GID 65534, and fresh output path. No retry.
- **D:** WSLc tests 8/8 PASS; candidate exit 0; independent auditor exit 0 with `PASS_PROBE_CONTRACT_SCOPED`, 3 seeds, 0 errors. Candidate raw SHA-256 `17ef7a6e53ae51014d91164af8e343d92f3354f17bebdee72fcfa262754e63d1`; audit SHA-256 `1b1cc271f5aab159f7ddad799aadc4036e68083585382c7589369e766663da36`. The outputs byte-match the earlier host-only construction outputs.
- **C:** This is a CPU-only runtime/construction validation of A02, not an additional LoRA experiment. WSLc reported `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` No GPU, CUDA, optimizer, training, model, GUI, or network access was used. Source/data are the same pinned bytes; only execution runtime differs from the prior host construction.
- **U:** Establishes that the A02 data-contract construction and audit execute successfully in the cached WSLc image. It does not establish online LoRA adaptation quality, forgetting behavior, GPU execution, or the formal #6354 hypothesis. Formal CUDA candidate/auditor remain unrun and require their own current-main freeze and exact GPU coordination.

## Runtime and source identity

- Branch: `research/needle-role-context-probe-6354-a02-20261002`
- Branch HEAD: `af9a055df0454ddb11cb2f17e2b5094eb35578e4`
- Included current main: `a5756d9b31231a4d64268610236622ac44c36f1f`
- WSLc: `3.0.1.0`; image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; cached image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`; linux/amd64.
- Frozen source hashes: candidate `8fb6180fb36302e2b29beae9a0e8a0106b8cb69eef7869595c4637268697deb9`; auditor `9246b34db0cbf2ea8d5841602bfecf39661d668fb009d9027c62ccaa34bdbdd6`; tests `26860d83c363871ec743bd272e852511f96050ff914aad36c2fc3abd188f50f7`.
- Dataset Git blob: `a11d8f9d231a035e65b7bc78b4b1a8e7cb5d9285`; canonical SHA-256 `5865040abbc60d79f138e81bf7e06bf6f885e66b5e29c9810ea8f599bad77685`.

## Invocation record

Construction tests (one container, exit 0):

```powershell
wslc run --rm --pull never --network none --cpus 0.25 --memory 512M --user 65534:65534 --mount "type=bind,source=<branch-worktree>,target=/src,readonly" --workdir /tmp python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B -m unittest discover -v -s /src/research/analysis/needle_role_conflict_probe_6354_a02 -p 'test_*.py'
```

Candidate (one separate container, exit 0; stdout is the raw digest above):

```powershell
wslc run --rm --pull never --network none --cpus 0.25 --memory 512M --user 65534:65534 --mount "type=bind,source=<branch-worktree>,target=/src,readonly" --mount "type=bind,source=<fresh-output>,target=/out" --workdir /tmp python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /src/research/analysis/needle_role_conflict_probe_6354_a02/candidate.py --dataset /src/research/system1/needle_role_context_online_lora_6321_v1_20261002/construction-01/dataset.json --out /out/raw.json
```

Independent auditor (one separate container after candidate exit 0; stdout `PASS_PROBE_CONTRACT_SCOPED`):

```powershell
wslc run --rm --pull never --network none --cpus 0.25 --memory 512M --user 65534:65534 --mount "type=bind,source=<branch-worktree>,target=/src,readonly" --mount "type=bind,source=<fresh-output>,target=/out" --workdir /tmp python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /src/research/analysis/needle_role_conflict_probe_6354_a02/audit.py --dataset /src/research/system1/needle_role_context_online_lora_6321_v1_20261002/construction-01/dataset.json --raw /src/research/analysis/needle_role_conflict_probe_6354_a02/construction_wslc_01/raw.json --out /out/audit.json
```

The placeholder mount paths above identify the exact host worktree/output directory used in this run; they are abbreviated for portability. WSLc `ps` was empty immediately before candidate and auditor execution. `nvidia-smi` showed the RTX 3080 at 0 MiB / 0% before the run; this CPU-only package did not request the GPU.

Raw and audit JSON are retained beside this report. The earlier A02 `FREEZE.json`, host raw/audit, and allocation-01 dataset remain unchanged. This report is an additive runtime-validation supplement, not a revision of the original frozen host allocation.
