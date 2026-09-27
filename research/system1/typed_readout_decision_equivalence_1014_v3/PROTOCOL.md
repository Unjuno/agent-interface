# Issue #4652 protocol

## H — hypothesis

Full-prefill and shared-prefix-cache execution select the same answer among
token IDs 15–22 for all 1,024 questions in the immutable 64×16 synthetic corpus.

## T — allocation

Reuse only the pinned Qwen2.5-0.5B-Instruct revision and weight digest,
tokenizer, FP16 dtype, PyTorch/Transformers/CUDA stack, derived Docker image,
and the retained Windows CRLF corpus SHA `85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c`. The exact bytes are included under `corpus_source/`; the canonical LF Git blob has SHA `c70d4ba3…`. See `CORPUS_REPRODUCTION.md`.
No download, model,
prompt, corpus, tokenizer, dtype, or image changes. Run locally on the RTX 3080
inside network-disabled Docker with read-only model/data/source mounts.

Excluded construction checks identity and token IDs, corpus dimensions, exact
effective token concatenation, finite eight-score vectors, isolated suffix
cache use, and rejection of stale generation/foreign bundle/changed prefix.
It does not compare categorical winners and contributes no formal row.

Freeze source and environment hashes; read them back from GitHub before formal
execution. Check local GPU occupancy immediately before starting. Then run one
bundle-major, slot-major paired allocation over all 1,024 questions. Prefill
each bundle prefix once for the cached arm. For every suffix, run the full
prefix-plus-suffix forward and a private-copy cached suffix forward, retain all
eight FP32 scores and decision margins, and alternate arms in a fixed order.
No retry, replacement, exclusion, tuning, or post-result change. Run the
independent raw-only audit in a separate network-disabled GPU container.

## D — gates

- `PASS_TYPED_DECISION_EQUIVALENCE_1024`: 1,024 unique complete pairs; every
  selected winner is one of IDs 15–22 and every full/cached winner matches;
  construction controls pass; independent audit errors are zero.
- `FAIL_TYPED_DECISION_DIVERGENCE`: any winner differs; preserve the exact first
  complete output and do not retry.
- `STOP_CONSTRUCTION`: any identity, corpus, token-boundary, cache-isolation,
  or cache-binding control fails before formal execution.

Score vectors are retained in full. No absolute/relative score gate applies in
this categorical-only successor. Timing is descriptive only and cannot support
a speedup claim.

## C / U

Both arms share exact inputs, checkpoint, tokenizer and FP16 settings; only
prefix reuse differs. One synthetic corpus, one checkpoint/software stack and
one GPU do not establish semantic correctness, task success, real-app behavior,
other-device behavior, cache speedup, execution authority, or product readiness.
The independent auditor checks reproducibility/integrity, not authenticity of
the model or corpus.
