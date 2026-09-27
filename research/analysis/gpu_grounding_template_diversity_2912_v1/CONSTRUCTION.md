# Issue #4546 construction record

## Environment preflight

- Host has RTX 3080 Laptop GPU, 16 GiB VRAM, Python 3.11.9, PyTorch 2.5.1+cu121, CUDA 12.1 and Pillow 10.4.0. A simple `nvidia/cuda:12.4.1-base-ubuntu22.04` container with `--gpus all` reported the same RTX 3080 and 16 GiB. A `python:3.11-slim` container runs with `--network none`, but has no torch, Pillow or numpy. The compatible GPU-enabled PyTorch image was not cached; registry pulls stalled and were stopped. Exact boundary is captured in `environment.json`.
- Host showed 265.1 GiB free on C: and 16 GiB total GPU memory. This was a preflight only, not evidence that the experiment passed.

## Mandatory deterministic operator probe

The #4482 TinyGrounder family uses two Conv/ReLU/MaxPool stages, `AdaptiveAvgPool2d((8,10))`, and a `1280 -> 32 -> 2` head on `[16,1,100,160]` inputs. Forward produced `[16,2]`. With `CUBLAS_WORKSPACE_CONFIG=:4096:8`, deterministic algorithms enabled, cuDNN deterministic and benchmark disabled, and TF32 disabled, backward stops with:

```text
RuntimeError: adaptive_avg_pool2d_backward_cuda does not have a deterministic implementation, but you set 'torch.use_deterministic_algorithms(True)'.
```

An independent minimal CUDA tensor using only `adaptive_avg_pool2d(...).sum().backward()` produces the same error. This isolates the failure to the required pooling backward kernel, not the CNN shape or dense-layer CuBLAS workspace. The probe was on host-local CUDA because only a CUDA base diagnostic container was immediately available; this host fallback is explicitly allowed by Issue #4546. No RNG seed, training batch, optimizer, or update was invoked.

## Decision

Construction gate failed; retain `STOP_CUDA_DETERMINISTIC_ADAPTIVE_POOL_BACKWARD`. Formal invocation count: 0. Optimizer steps: 0. No training/evaluation dataset was rendered, no arm executed, no candidate was emitted, and no hypothesis result exists. Do not silently substitute pooling, disable strict determinism, upgrade dependencies, rerun, or promote. A changed operator/framework requires a successor freeze.
