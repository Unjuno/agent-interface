# Construction record — Issue #4546

Date: 2026-09-27 JST. Source main: `13cd6645b1bdd266bbe010f82ebcec2a573c23ed`.

## Corpus construction

- 12 locally authored synthetic template families; 8 train families / 4 whole-family held-outs; 20 deterministic variants per family.
- 240 distinct image SHA-256 values; no duplicate PNG bytes. All image sizes are 1280x800. Manifest SHA-256: `bff0c9edc8f4b1a0d1fcb7d3577faba6d752e38bb8182879a4af0ff3f7ea2d8a`.
- Construction audit re-opened and hashed all 240 files, independently recomputed source template hashes and renderer-derived point labels, and checked family/source separation. Corrupted label and split controls were rejected.
- Renderer is Pillow 10.4.0 with fixed font, color, jitter, resizing and PNG parameters. Images are explicitly synthetic; they are not real-app examples.

## Model and safety construction

- `py_compile`: PASS.
- `test_construction.py`: 7/7 PASS, including CPU full-model shape and pooling-oracle checks, exact candidate schema/bounds controls, independent metric-auditor positive/corruption controls, deterministic rendering checks, and repeated CUDA forward/backward equality.
- The CUDA determinism test used the RTX 3080 Laptop GPU with `CUBLAS_WORKSPACE_CONFIG=:4096:8`, deterministic algorithms enabled and TF32 disabled. It performed zero optimizer updates.
- Formal invocations: 0. No model training, evaluation allocation, GUI input, or authority grant has occurred.

## Local runtime boundary

Host probe: Python 3.11.9, NumPy 2.4.6, Pillow 10.4.0, PyTorch 2.5.1+cu121, CUDA 12.1; `torch.cuda.is_available() == true`; NVIDIA GeForce RTX 3080 Laptop GPU, 16 GiB, driver 581.57. The GPU was idle at the probe (11 MiB reported allocated, 0% utilization).

A no-network run of the pre-existing `needle-pilot05:local` Docker image found PyTorch 2.5.1+cpu and CUDA unavailable in that image. This is not a claim that Docker GPU passthrough is impossible. To keep all computation on the PC and avoid installing another large CUDA stack, the frozen allocation uses the already-installed host-local CUDA runtime. No hosted or remote training workflow was used.

Raw compile/test/runtime/Docker probe outputs are retained in `construction/01/`. Exact source and environment pins are recorded in `FREEZE.json`. These are preformal construction gates only; they do not authorize or count as a training result.
