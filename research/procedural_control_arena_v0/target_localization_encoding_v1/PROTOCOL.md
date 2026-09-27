# Protocol — Issue #4666 first paired visual-localization rung

## H

For identical v0-generated target scenes and the same local vision model, an
80-pixel coordinate-grid presentation lowers point-to-target-center error while
preserving exact color+shape selection and points that would hit the target in
the Arena engine.

## T

- Allocation: `arena-v0-target-grid-4666-v1-20260927-01`.
- Formal seeds: 8866601 through 8866612, fixed difficulty 0.35. Excluded
  construction/warmup seed: 8866600. No replacements.
- Model: `qwen2.5vl:7b`, local Ollama model digest
  `5ced39dfa4bac325dc183dd1e4febaa1c46b3ea28bce48896c8e69c1e79611cc`.
- Container: `python@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`
  (`linux/arm64`, locally cached; no pull/install).
- Per seed, construct one v0 target stage from the full deterministic episode;
  render the initial object geometry once for each arm. The model receives only
  a PNG and identical target wording. Candidate is the same scene with faint
  80px grid lines and numeric axis labels; coordinate mapping is identity.
- Two stateless `/api/generate` calls per seed, temperature 0, fixed sampler
  seed 424242, JSON output `{color,shape,x,y}`. Counterbalance call order by
  seed index. No action is emitted. Preserve full request/response, images,
  truth, model timing and API usage fields.
- One construction-only RAW/GRID80 pair on seed 8866600 before freeze; one
  excluded RAW warmup on seed 8866600 at the start of the formal invocation.
  Neither is scored or pooled. Formal invocation is exclusive-create and one
  shot; preserve partial raws as STOP on any error.
- Docker bridge is necessary because the host Ollama service is unreachable
  from an internal Docker network. Runner source references only the host-local
  Ollama URL. This is not a network-egress isolation claim.

## D

`PASS_GRID80_LOCALIZATION_SIGNAL_SCOPED` only if all 12 exact pairs validate,
GRID80 has at least the RAW exact target-selection and Engine-hit counts, the
GRID80 pooled median center error is at most 80% of RAW, and GRID80 has lower
center error in at least 8/12 pairs. Otherwise retain `HOLD_NO_PREREGISTERED_GAIN`
or a typed integrity STOP. No post-result threshold changes.

## C

The same generator, seed, initial scene geometry, semantic instruction, model
and decoding are paired; only the image overlay differs. Deterministic
rasterization is not Tk screenshot equivalence. Evaluation order can still
interact with host/model load even though each request has an independent
context; order is counterbalanced.

## U

This first rung measures static visual target proposal, not click success,
motor accuracy, dynamic targets, live freshness, realtime latency, held-out
compositions, full B0/C1 task effect, or transfer. One model/host and twelve
pairs do not establish a general effect. The formal model itself may not be
considered a frontier-model substitute for later issue gates.
