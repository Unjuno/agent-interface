# Environment — Issue #4639

This successor reused the predecessor's pinned local model and corpus read-only.
No network access was enabled in the experiment containers.

- Host GPU: NVIDIA GeForce RTX 3080 Laptop GPU (16 GiB class).
- Container base: `pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`.
- Derived image ID: `sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261`.
- PyTorch 2.5.1+cu121; CUDA 12.1; Transformers 5.16.1; Safetensors 0.8.0.
- Model revision: `7ae557604adf67be50417f59c2c2f167def9a775`.
- Model weight SHA-256: `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
- Corpus SHA-256: `c70d4ba3d06dec161fdc8d3f5e5312fbe3ff0af1c1a36cdcb0dc0e290efe27fd`.

Containers used `--gpus all --network none --read-only --cpus 2 --memory 8g
--pids-limit 64`, a bounded temporary filesystem, read-only source/model/corpus
mounts, and a dedicated writable output mount. Full image/model/corpus provenance
is retained in `../typed_readout_prefix_gpu_1014_v1/`.
