# #4561 template-diversity local grounder experiment

This bundle is a reproducible, local-only synthetic computer-vision study. It trains a tiny CNN from random initialization on rasterized form templates and measures paired field/submit localization on held-out template families. It does not invoke a GUI, remote model service, or pretrained model.

## Frozen question and design

See [`PREREGISTRATION.md`](PREREGISTRATION.md) for H/T/D/C/U, split, update budget, strict acceptance and pass/hold gates. The 12-family renderer, model, cell-to-source-coordinate adapter, strict compiled-form validator, one-shot CUDA runner, independent raw-results auditor, and construction/mutation tests are included in this directory.

The deterministic fixed-matrix average pool is used because the predecessor's adaptive-pool backward was not deterministic on this CUDA stack. It is mathematically checked against PyTorch's adaptive average-pool CPU oracle; CUDA forward and input-gradient repeatability are checked before formal training.

## Construction checks

Verified in the pre-existing image `pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime` (Pillow 10.2.0; image ID is recorded in `FREEZE.json`) with an RTX 3080 Laptop GPU, strict deterministic algorithms, and no network:

```powershell
docker run --rm --gpus all --network none `
  -e CUBLAS_WORKSPACE_CONFIG=:4096:8 `
  -v "${PWD}:/work:ro" -w /work `
  pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime `
  python -m unittest -v test_construction.py test_audit.py
```

The formal runner writes only beneath `ISSUE4561_OUTPUT` (default `results/formal01`) and refuses to overwrite an existing allocation directory. The container source mount can therefore remain read-only while a separate output bind mount is writable. Formal may execute exactly once, only after the GitHub freeze and construction checks pass. Do not rerun, tune, or replace the frozen matrix after observing formal results.

After the one formal run, audit the retained JSON independently:

```powershell
docker run --rm --network none -v "${PWD}:/work:ro" -w /work `
  pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime `
  python audit.py /work/results/formal01/results.json
```

`REPORT.md` is written only after formal output and independent audit are retained. A pre-formal construction stop must instead be recorded as `FORMAL_FAILURE.md`, with zero formal invocations and zero optimizer steps.
