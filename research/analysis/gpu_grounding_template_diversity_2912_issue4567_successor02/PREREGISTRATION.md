# Preregistration — Issue #4567

Allocation: `gpu-grounding-template-diversity-2912-successor-02`
Source main commit: `d823943868ff73e81fed278e9a00ca6422fdf50d`
Predecessor: #4546, immutable `STOP_INPUT_PATH_ERROR`; no results transfer.

## H / T / D / C / U

**H — hypothesis.** At fixed model, per-seed initialization, optimizer-step count and total sampled examples, training on eight synthetic form-template families rather than two may improve exact field/submit coordinates on four wholly held-out synthetic families. This is only a test of the fixed synthetic distribution.

**T — treatment.** Reuse, without alteration, the 12-family/240-image synthetic corpus already constructed for #4546. The split remains eight train families and four whole-family held-outs. Three seeds (29121–29123), paired initial state, common sampling stream, two-vs-eight training families, batch 16, 500 Adam steps at 0.001, SmoothL1 beta 0.02. RTX 3080 Laptop GPU with the locally installed CUDA/PyTorch stack only; no hosted or remote compute. This is a new one-shot allocation and new result path `results/formal01/`.

**D — decision.** Before training, independently resolve all 240 manifest image paths under `corpus/`, verify every byte hash, reject traversal, pass CPU construction/auditor controls, verify source hashes by GitHub MCP readback, ensure #4567 has no competing allocation, and verify the local GPU is no longer in use by #4205 using a fresh device/occupancy capture. If any gate fails, record STOP with no training. After gates pass, one formal invocation only, no retries. PASS requires broad exact-coordinate rate >=0.90 in every held-out family and >=0.10 absolute aggregate improvement over narrow, 100% schema/bounds validity and a zero-error independent audit. Any other completed outcome follows the prior frozen outcome matrix; no result grants action authority.

**C — controls/boundaries.** Keep model, initial weights per seed, preprocessing, optimizer, sampled-example count, updates, evaluation set, rounding, and strict validator fixed. Do not tune against held-out outcomes, alter predecessor evidence, interact with a GUI, or claim real-application transfer. The synthetic corpus is reused and does not constitute a fresh independent dataset.

**U — unknowns.** Whether the fixed CNN can learn these exact coordinates; whether synthetic template diversity is informative; whether it has any relation to real applications; and whether local GPU availability becomes conflict-free for the one-shot run.

## Non-retry and serialization rule

An invocation consumes the allocation even if it exits before its first optimizer update. Never retry or overwrite `results/formal01/`. Before setting `LOCAL_GPU_SERIALIZATION_ACK=4567-idle-confirmed`, confirm #4205 has stopped using the local GPU and record fresh `nvidia-smi` output. Hosted workflows are prohibited.

## Commands

CPU-only path and construction gate:

```powershell
$env:PYTHONPATH='research/analysis/gpu_grounding_template_diversity_2912_v2;research/live_control'
python -m unittest test_construction.ConstructionTests -v
```

Full deterministic CUDA construction check (only after no other task is using the GPU):

```powershell
$env:CUBLAS_WORKSPACE_CONFIG=':4096:8'
python -m unittest discover -s research/analysis/gpu_grounding_template_diversity_2912_v2 -p 'test_construction.py' -v
```

Formal command, once only after all GitHub and local GPU gates pass:

```powershell
$env:CUBLAS_WORKSPACE_CONFIG=':4096:8'
$env:LOCAL_GPU_FORMAL_ACK='4567-one-shot'
$env:LOCAL_GPU_SERIALIZATION_ACK='4567-idle-confirmed'
python research/analysis/gpu_grounding_template_diversity_2912_v2/train_eval.py --repo . --out research/analysis/gpu_grounding_template_diversity_2912_v2/results/formal01
python research/analysis/gpu_grounding_template_diversity_2912_v2/audit.py --repo . --result research/analysis/gpu_grounding_template_diversity_2912_v2/results/formal01/results.json
```
