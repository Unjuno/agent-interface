# Container materialization stop — GPU photometric experiment

2026-09-21 JST. No model training or evaluation had begun.

- Docker Desktop 4.91.0 / Engine 29.8.0 was started locally.
- `nvidia/cuda:12.4.1-base-ubuntu22.04` with `--gpus all` ran `nvidia-smi` and saw the RTX 3080 Laptop GPU (16 GiB). GPU passthrough works.
- Pulling `pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime` did not complete. Local C: free space fell from 7,437,275,136 bytes to 784,015,360 bytes; the pull was interrupted to prevent exhausting the PC disk. No model process ran and no image tag was available.
- Host Python 3.11 already has PyTorch `2.5.1+cu121`; `torch.cuda.is_available()` is true and reports the same RTX 3080, CUDA 12.1, driver 581.57.

Disposition: `STOP_CONTAINER_IMAGE_STORAGE` for container materialization. The same single frozen model allocation proceeds only under the explicitly amended local-host CUDA environment in `PREREGISTRATION.md`; this changes no source rows, split, model, optimizer, augmentation, evaluation, routing, or acceptance gate. It is not represented as a container result.
