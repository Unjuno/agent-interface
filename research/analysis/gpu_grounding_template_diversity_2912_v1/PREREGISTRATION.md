# Preregistration — Issue #4546

Allocation: `gpu-grounding-template-diversity-2912-successor-01`
Source main: `13cd6645b1bdd266bbe010f82ebcec2a573c23ed`
Disposition before training: `PREFORMAL_CONSTRUCTION`

## Question and hypothesis

At fixed model, initialization seed, optimizer, number of sampled examples, and optimizer steps, does exposure to eight training template families rather than two improve exact field-and-submit coordinate predictions on four wholly held-out synthetic form-template families? This is a synthetic visual-regression experiment only.

## Frozen treatment

- 12 distinct template specifications `T01`–`T12`, 20 deterministic variants each; 8 train families and 4 held-out families are specified before rendering.
- Three training seeds: 29121, 29122, 29123.
- Narrow arm: training examples from `T01` and `T02` only. Broad arm: training examples from all `T01`–`T08`.
- Both arms use the same model, initial state for a given seed, a common seeded uniform-sampling stream, batch size 16, 500 optimizer steps, Adam at 0.001, and Smooth L1 coordinate loss. Repeated draws are allowed; no evaluation family enters training.
- Held-out evaluation: the same 20 images from each of `T09`–`T12` for both arms and all seeds (80 rows/arm/seed).
- Rasterizer: Pillow 10.4.0; template coordinates 320x200, raster canvas 640x400, source canvas 1280x800; nearest-neighbor source enlargement; grayscale bilinear 160x100 model input. Targets are renderer-derived field/submit centers quantized to the representable 8-source-pixel grid.
- Model: two Conv2d/ReLU/MaxPool blocks (1→8→16 channels), fixed separable 25x40→8x10 pooling, 1280→32→4 sigmoid coordinate head. No pretrained weights or external model downloads.
- Device: this PC's RTX 3080 Laptop GPU using the already-installed Python 3.11.9, NumPy 2.4.6, Pillow 10.4.0, PyTorch 2.5.1+cu121, CUDA 12.1 environment. `CUBLAS_WORKSPACE_CONFIG=:4096:8` must be set before Python starts. Deterministic algorithms on; TF32 off. A no-network probe of the pre-existing `needle-pilot05:local` image found PyTorch 2.5.1+cpu and no CUDA device; this does not establish Docker GPU passthrough. Use the known-good host-local CUDA stack rather than install a second multi-gigabyte CUDA stack. No remote training service or hosted workflow.

## Decision rule

Construction must pass the data/hash/split/label checks, strict-validator positive and corruption controls, CPU model shape test, and repeated deterministic CUDA forward/backward test before any formal optimizer step.

Exactly one formal runner invocation contains all three seeds and both arms. No retries, seed substitutions, post-result tuning, or additional formal calls. An independent auditor recomputes source hashes, template separation, schema/bounds acceptance, exact coordinate accuracy, counts, and disposition.

- `PASS_TEMPLATE_DIVERSITY_BENEFIT`: broad arm reaches >=0.90 exact coordinate accuracy in each of four held-out families and exceeds the paired narrow-arm aggregate by >=0.10, with 100% schema/bounds validity and zero audit integrity errors.
- `HOLD_NO_CLEAR_DIVERSITY_BENEFIT`: broad arm meets all four per-family >=0.90 gates but aggregate improvement is <0.10.
- `FAIL_HELDOUT_COORDINATE_QUALITY`: broad arm misses any per-family >=0.90 gate, or a formal audit finds a schema/bounds-invalid candidate.
- `STOP_PREFORMAL_*`: a source, device, determinism, or protocol gate fails before the first formal optimizer step. Preserve the exact evidence; do not relabel as a scientific result.

Schema validity and coordinate correctness are separate: schema-valid wrong coordinates are counted as model errors. No prediction is sent to a GUI, and no local model receives authority.

## Provenance and non-claims

The 240 images are deterministically rendered from local synthetic specifications; they are not 240 independent real-world sources. The unit of split is the entire template family, not a screenshot variant. Results cannot establish transfer to real forms, unseen real applications, calibration, user task success, action safety, runtime benefit, or product readiness. Prior #2912/#4482 data and outcomes remain unchanged.

## Frozen commands

Construction (before the one formal invocation):

```powershell
$env:CUBLAS_WORKSPACE_CONFIG=':4096:8'
py -3.11 -m unittest discover -s research/analysis/gpu_grounding_template_diversity_2912_v1 -p 'test_construction.py' -v
```

Formal runner (exactly once, after hashes are read back from the issue branch; output path must be absent/empty):

```powershell
$env:CUBLAS_WORKSPACE_CONFIG=':4096:8'
$env:LOCAL_GPU_FORMAL_ACK='4546-one-shot'
py -3.11 research/analysis/gpu_grounding_template_diversity_2912_v1/train_eval.py --repo . --out research/analysis/gpu_grounding_template_diversity_2912_v1/results/formal01
py -3.11 research/analysis/gpu_grounding_template_diversity_2912_v1/audit.py --repo . --result research/analysis/gpu_grounding_template_diversity_2912_v1/results/formal01/results.json
```

Do not rerun the formal runner if it exits nonzero, produces partial output, or the independent audit fails. Retain its exact process evidence as STOP/HOLD and use a separately approved successor allocation for any further model execution.
