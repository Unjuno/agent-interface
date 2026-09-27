# Environment and asset identities — Issue #4652

- Host GPU: NVIDIA GeForce RTX 3080 Laptop GPU, 16 GiB; host driver 581.57.
- Container engine: Docker Desktop 29.8.0, context `desktop-linux`.
- Base: `pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`.
- Derived local image ID: `sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261`.
- Stack: PyTorch 2.5.1+cu121, CUDA 12.1, Transformers 5.16.1, Safetensors 0.8.0.
- Model: `Qwen/Qwen2.5-0.5B-Instruct`, revision `7ae557604adf67be50417f59c2c2f167def9a775`, Apache-2.0; `model.safetensors` SHA-256 `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
- Corpus: exact Windows CRLF input retained at `corpus_source/corpus.jsonl`, 270,292 bytes, SHA-256 `85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c`. Its canonical LF Git source blob is 270,228 bytes, SHA-256 `c70d4ba3d06dec161fdc8d3f5e5312fbe3ff0af1c1a36cdcb0dc0e290efe27fd`.

Construction, formal runner and independent auditor all hash-check the local
model weights and corpus. Containers use network none, read-only root/source,
model and corpus mounts, 2 CPUs, 8 GiB memory, 64 PIDs and 256 MiB tmpfs. Only
the output directory is writable. GPU execution is local and containerized.
