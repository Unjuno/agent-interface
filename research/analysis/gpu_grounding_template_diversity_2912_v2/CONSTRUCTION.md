# Construction record

Construction only; not a scientific result.

- Local device: NVIDIA GeForce RTX 3080 Laptop GPU, exposed to Docker via `--gpus all`.
- Image: `pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime`, Pillow 10.2.0, local image ID `sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`.
- Network: disabled for test execution (`--network none`). Source bind mount read-only.
- Determinism: `CUBLAS_WORKSPACE_CONFIG=:4096:8`, PyTorch deterministic algorithms, cuDNN deterministic, benchmark/TF32 off.
- Command: `python -m unittest -v test_construction.py test_audit.py`.
- Result: 9 tests passed, 0 failed. Tests include exact pre-frozen 48-image PNG/pixel/label hashes, fixed-pool CPU oracle max error ≤1e-6, complete network shape/loss/backprop, renderer and split determinism, validator corruption rejection, repeated CUDA model forward/input gradients, positive and negative audit fixtures, and seven mutations rejected.
- Optimizer training steps: 0 at this construction gate. No formal invocation, result corpus, remote service, pretrained model, GUI, or app action occurred.

The GPU operator failure retained by #4546 is avoided without weakening determinism: the implementation uses the exact fixed separable pooling matrix already present in merged #4482 evidence, then verifies this fresh model's forward/backward determinism in the selected container before proceeding.

A local derived-image attempt to install Pillow 10.4.0 failed because the container package index returned no available distributions. No network or package change is needed: the already-cached pinned PyTorch CUDA image contains Pillow 10.2.0, so the renderer version was pinned to that existing version before the corpus manifest and formal freeze were generated. No optimizer or formal training step occurred during the failed image build.
