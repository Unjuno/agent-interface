# Guarded inline skill cache — formal result

Issue #4260. Decision: **PASS_GUARDED_INLINE_SKILL_CACHE_SCOPED**.

## First frozen outcome

- formal rows: 48/48
- formal invocations/reruns/replacements/tuning: 1/0/0/0
- wrong application effects: 0
- candidate warm cache hits: 9/9 expected warm calls
- candidate deoptimizations: 15 (all cold/incompatible/unseen/generation-mismatch calls)
- GENERIC_PATH full-frame semantic scan work: 5,529,600 pixels
- GUARDED_INLINE_CACHE full-frame semantic scan work: 3,456,000 pixels
- candidate guard acquisition: 9,600 pixels
- full-frame semantic-scan reduction: 37.5%
- independent raw audit: errors=[]
- coherent corruption controls rejected: 8/8
- every click produced independently journaled SAVE_ACTIVATED and terminal Button1 neutral.

## Interpretation

In this one real Xvfb/Tk call-site fixture, K=2 guarded specialization reused current-state-compatible target coordinates on the three preregistered warm phases per repetition. Guard mutation, unseen shape, and pixel-old-looking but generation-new state never reused the specialization; they deoptimized to the unchanged full current semantic resolver. The measured benefit is deterministic generic pixel-scan work, not frontier-model tokens or general GUI latency.

## Preserved failures

Construction-01 STOP_SETUP_XAUTHORITY and construction-02 STOP_SETUP_XAUTHORITY_PARENT_ENV occurred before any operation row and remain retained. Construction-03 was eligible but excluded from formal. No formal rerun or result-driven tuning occurred.

## Evidence

- SOURCE.tar.xz SHA-256: `5a5f026eaec9ea109b9fca3518baae4f45dd2ba3aa1319cce4804229290b5e76`
- formal RAW.json SHA-256: `6297bef455e58860080515538971b7d1e6e498473206c60cc19eaa186812784e`
- AUDIT.json SHA-256: `66be7f0a9fdf8aa095a5bd170b6a1ffa397a785ce5226a9d81e9cf0275ced4c3`
- CONTROLS.json SHA-256: `c934b54d2eff425af9a9492cee295d845dd3ea2c628678e42cce79cfd2d01ebe`
- full lossless formal archive SHA-256: `646c440a6d64c6558da0d226e69c100a079b77b9342f67fcca3b5c049b8ee845`
- fresh extraction reproduced AUDIT and CONTROLS byte-for-byte; no live rerun.

## Scope / C / U

The guard is an exact 20x20 marker hash plus trusted generation in a cooperative fixture. This does not establish automatic guard synthesis, semantic identity under hidden dependencies, token savings, model quality, cross-application transfer, or production readiness. K=2 can thrash on richer polymorphism.
