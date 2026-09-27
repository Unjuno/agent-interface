# Issue #4652 preregistration

This tests only whether full-prefill and shared-prefix-cache execution choose the same typed answer over the entire already-frozen synthetic corpus. Preserve #4623's full-vocabulary STOP and #4639's eight-code score-tolerance STOP unchanged. The threshold failure in #4639 is not being waived: this issue's observable is categorical winner equality only.

## H — hypothesis

Across all 1,024 questions (64 existing bundles × 16 suffixes), the selected winner among token IDs 15–22 is identical between full-prefill and isolated shared-prefix-cache execution on the pinned local Qwen2.5-0.5B-Instruct revision and RTX 3080.

## T — treatment

- Frozen intake main: `27c7f38c9bb072e0462b07edd06d6cf9ef46bb0a`; additive branch `research/typed-decision-equivalence-4652-v1-20260927`; path `research/system1/typed_decision_equivalence_4652_v1/`.
- Exact locally cached model revision `7ae557604adf67be50417f59c2c2f167def9a775`, weight SHA-256 `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`; exact already-cached image ID `sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261`; corpus SHA-256 `c70d4ba3d06dec161fdc8d3f5e5312fbe3ff0af1c1a36cdcb0dc0e290efe27fd`.
- Model, source, and corpus read-only; local Docker only, network disabled; RTX 3080 passthrough. One pre-formal construction gate followed by exactly one formal invocation; no downloads, training, tuning, data/model/prompt changes, exclusions, or retries.
- Before formal: recheck GPU idle; verify model, framework, image, answer token IDs `[15..22]`, corpus shape/hash, all 1,024 token concatenation boundaries, per-suffix cache isolation, and stale/foreign/changed-prefix rejection. Freeze sources and hashes on GitHub and read them back first.
- Formal schedule: 64 bundles in order; for each bundle, prefill its prefix once for cache arm; 16 slots in order; each question uses paired full-prefill then private-copy cached execution. Retain both eight-value FP32 score vectors, winner IDs, top-two margins, token/prefix digests, and durable row journal.
- A separate network-disabled GPU audit container reloads the exact local model and independently reimplements/recomputes both forwards for every retained pair. It imports no runner or cache helper.

## D — decision

- PASS only for exactly 1,024 complete paired records, all 1,024 winners equal, outputs limited to IDs 15–22, all controls pass, and independent audit `errors=[]`.
- Any winner divergence is `FAIL_TYPED_DECISION_DIVERGENCE`; preserve the first complete raw outcome, no retry/exclusion.
- Any preformal identity/token/cache-binding failure is `STOP_CONSTRUCTION` and formal must not start.
- Scores, margins, and latency are retained for audit/context only; no score tolerance or speed claim is introduced.

## C — controls / alternatives

Both arms use identical frozen weights, token IDs, dtype, positions, masks, and order. Cached state is isolated by bundle and deep-copied per suffix. This answer-equivalence observable neither waives selected-score mismatch from #4639 nor establishes semantic quality or action authority.

## U — limits

One synthetic 64×16 corpus, one checkpoint/revision, one RTX 3080 and one image. Agreement is only execution-mode decision agreement on these 1,024 fixtures. It says nothing about semantic correctness, natural tasks, GUI performance, latency, other devices, training, or runtime authority.
