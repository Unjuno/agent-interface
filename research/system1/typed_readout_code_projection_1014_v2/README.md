# Typed answer-code projection successor — Issue #4639

This is a new allocation after #4623's full-vocabulary FP16 construction STOP.
It preserves that result unchanged and asks whether the exact eight-token output
boundary used by a typed readout is equivalent under shared-prefix caching.

The immutable input corpus and model asset remain in the merged predecessor
package at [`../typed_readout_prefix_gpu_1014_v1/`](../typed_readout_prefix_gpu_1014_v1/).
The corpus SHA-256 is
`c70d4ba3d06dec161fdc8d3f5e5312fbe3ff0af1c1a36cdcb0dc0e290efe27fd`; the
model revision, weight hash, license and CUDA image identity are recorded in
the predecessor's manifests. This package does not contain model weights or a
second corpus copy.

The observable is the eight selected answer-token logits and their argmax; the
other vocabulary logits are intentionally outside this successor's hypothesis.
The absolute and relative score tolerances remain the originally frozen 0.002.
This does not assess semantic quality, user tasks, GUI behavior, or execution
authority.

The formal block must not run unless excluded construction and independent
audit pass and exact source/readback hashes are frozen on the Issue #4639 branch.
