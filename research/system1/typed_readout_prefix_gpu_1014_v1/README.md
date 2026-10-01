# GPU shared-prefix cache reuse — Issue #4623

This additive package starts a fresh, one-model successor to #1014/#1033. The
only scientific factor is serial reuse of one exact prefix KV cache across
independent typed suffix questions. It is a mechanics study; it does not score
task semantics or authorize UI actions.

## Frozen identity

- Model: [`Qwen/Qwen2.5-0.5B-Instruct`](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)
  at `7ae557604adf67be50417f59c2c2f167def9a775` (Apache-2.0).
- Runtime base: `pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`.
- Transformers: 5.16.1; PyTorch: 2.5.1+cu121; inference dtype: FP16.
- GPU: RTX 3080 Laptop GPU, 16 GiB; exact driver/runtime and image IDs are
  captured in the run records.

The model weights are not committed. A local, hash-verified snapshot is mounted
read-only at `/models/model`. Formal containers have no network, immutable
root/source, and a dedicated output mount.

## Allocation

The preregistration is Issue #4623. Sixty-four deterministic input bundles each
contain sixteen separate suffix questions over a shared state prefix. Arm A
prefills the full prefix+suffix per question. Arm B prefills once per bundle and
evaluates each suffix serially against an isolated copy of that bundle's prefix
cache. Both arms use the same model, effective token IDs, positions, masks,
answer token IDs, FP16 dtype and serial schedule. There is no training,
quantization, suffix batching, compilation, GUI, provider, task input, or
execution authority.

The formal block must not start until source, corpus, model and environment
hashes are frozen/read back on the issue branch and excluded construction
checks pass. The first formal outcome is retained without retries. See the
issue for decision gates and limits.
