# Issue #4639 protocol

## H — hypothesis

Full-prefill and shared-prefix-cache execution produce the same winning answer
within the frozen eight-token typed vocabulary and selected-code logits within
absolute and relative 0.002, even though #4623 stopped on full-vocabulary FP16
logit deltas.

## T — construction scope

Use only the exact #4623 model, revision, weight digest, Transformers/PyTorch
versions, CUDA image and 64×16 corpus. No download, new model, corpus/prompt
edit, training, tuning, GUI, user data, provider call or action authority.
Compare independent full-prefill with one prefix prefill plus serial suffixes
against an isolated clone of the bundle's immutable prefix cache. Project both
logit vectors onto answer token IDs `[15,16,17,18,19,20,21,22]`.

Excluded construction covers three bundles × three suffixes. Check exact token
concatenation; every answer spelling has its frozen distinct one-token ID;
projected score tolerance and answer winner equality; per-suffix cache
isolation; and bundle/generation/prefix binding controls for stale or foreign
cache handles. Any construction failure stops the allocation before formal
timing. Construction is excluded from formal denominators.

If construction and independent audit pass, freeze all formal source and
readback hashes, then make one formal call of 1,024 sixteen-question bundles
per arm in fixed interleaved order. No retries or post-result changes. Retain
every eight-score vector, selected answer, timing, miss/error, GPU sample,
stdout/stderr and exact invocation. The separate audit reimplements model
calls and recomputes every projected decision/tolerance and every retained row.

## D — gates

Mechanism PASS requires every formal selected-code argmax to match, all selected
score vectors within absolute and relative 0.002, all cache/vocabulary controls
fail closed, and an independent zero-error audit. A latency candidate also
requires shared-cache warm whole-bundle p95 ≤60 ms and at least 20% lower p95
than full-prefill. Report p50/p95/p99/max and misses for both arms; never divide
bundle latency by question count. Any miss is retained without gate changes.

## C / U

The full-vocabulary error may lie only on unused tokens, or may alter one of the
eight selected scores. Prefix cloning, suffix work and GPU scheduling may erase
prefill savings. One model, revision, synthetic corpus, image and RTX 3080 only;
no semantic quality, #1015 capability, natural app workflow, CPU/cross-device
SLO, GUI execution, authority, cost/energy or product claim. Hashes prove
integrity, not authenticity.
