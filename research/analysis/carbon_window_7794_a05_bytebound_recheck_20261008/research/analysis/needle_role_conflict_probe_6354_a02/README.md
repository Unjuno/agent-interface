# Issue #6354 — role-conflict probe contract successor (A02)

## H / T / D / C / U

- **H:** an explicit ambiguity probe is valid only when one identical binary feature vector is present in both roles and the independently derived labels disagree (`A=0`, `B=x[0]=1`).
- **T:** read the immutable #6354 construction dataset, choose one deterministic shared vector with `x[0]=1` per seed, emit a new probe packet, and independently audit the packet against the source dataset. The original allocation-01 dataset and freeze are inputs only and are never edited.
- **D:** accept only exact seed coverage, source digest, actual cross-role membership, target consistency, and contradictory labels for every probe; otherwise fail closed. Mutation tests cover equal labels, mismatched target, non-overlap, malformed vector, seed omission, and source-digest mismatch.
- **C:** finite synthetic binary vectors and target rules from #6354; this is a narrow data-contract correction, not a model run.
- **U:** no LoRA fit, optimizer update, CUDA/GPU, online learning, forgetting, latency, real task, or deployment claim. A pass would establish only that the explicit probe contract is constructible and independently auditable. It does not repair or replace #6354 allocation-01 or authorize the formal candidate.

## Provenance and execution state

Prepared from main `3f78141830f22462cbefd5a2fac906668339d9a4` in a distinct branch and path. After the host run, the branch was fast-forwarded to current main `a80fa420dd60da7caf90165263acf736801947a1`; the pinned allocation-01 dataset Git blob is unchanged. The input is the already-published immutable allocation-01 dataset. This successor exists because the original `role_conflict_probe` uses the all-zero vector, yielding A/B labels 0/0 despite the preregistration calling for a contradictory-label probe. Existing cross-role overlaps do not make that named probe correct.

The source dataset is pinned by its canonical JSON SHA-256 `5865040abbc60d79f138e81bf7e06bf6f885e66b5e29c9810ea8f599bad77685`; both candidate and independent auditor fail closed on a different dataset. Canonicalization matches the original freeze and avoids platform newline conversion changing the identity.

The candidate selects a shared feature vector with first coordinate 1 from each seed's immutable role splits and emits only a probe packet. The auditor is a separate stdlib-only entrypoint and reconstructs overlap/targets from the source dataset; it imports no candidate code. The construction test suite includes the original equal-label all-zero failure mode and positive/mutation controls.

Planned no-network WSLc construction suite (CPU only):

```powershell
wslc run --rm --pull never --network none --cpus 1 --memory 512M `
  --mount "type=bind,source=<repo-root>,target=/src,readonly" --workdir /tmp `
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f `
  python -B -m unittest discover -v -s /src/research/analysis/needle_role_conflict_probe_6354_a02 -p 'test_*.py'
```

After the construction suite passes in an assigned lane, run one candidate container against the fixed dataset path `research/system1/needle_role_context_online_lora_6321_v1_20261002/construction-01/dataset.json`, then one separate auditor container only if candidate exits 0. Each output path must be fresh; retries are zero. This packet is not the model candidate and must not be used to assert LoRA quality.

Host-only construction candidate/auditor passed once each; the raw and audit are retained in `construction_host_01/` and the scope is limited in `REPORT.md`. This is not a WSLc run. The CPU-only WSLc validation is still needed in the cached, pinned Python image with network disabled, and must not run until a compatible CPU/WSLc lane is explicitly assigned under #5085; an empty `wslc ps` snapshot is not a lane grant. Formal LoRA execution still requires a separate fresh GPU allocation, fresh source/data freeze and a separate raw-only auditor.
