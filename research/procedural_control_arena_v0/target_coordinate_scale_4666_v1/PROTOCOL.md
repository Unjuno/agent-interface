# Protocol — coordinate-scale successor to Issue #4666

## H

For the same target-stage image, expressing requested coordinates in normalized
`[0,1]` source coordinates rather than source pixels reduces out-of-frame
proposals and center error without reducing exact target identity or Engine
target hits.

## T

- Allocation: `arena-v0-coordinate-scale-4666-v1-20260928-01`.
- Excluded construction seed: 8866620. Formal seeds: 8866621–8866632, difficulty
  0.35. No replacement seeds.
- Each seed generates one deterministic RAW v0 target-stage image, passed
  byte-identically to both arms.
- `PIXEL` asks for source-image pixel `x,y`; `NORM01` asks for source-frame
  normalized `x,y` in `[0,1]`. Both retain the same JSON keys and target wording.
  NORM01 is mapped posthoc as `x_px=x_norm*639`, `y_px=y_norm*479`; values are
  never clipped. Out-of-range and out-of-frame proposals remain measured
  outcomes, not request-integrity errors.
- Local Ollama `qwen2.5vl:7b`, digest
  `5ced39dfa4bac325dc183dd1e4febaa1c46b3ea28bce48896c8e69c1e79611cc`;
  temperature 0, sampler seed 424242, `num_predict=128`.
- Counterbalanced arm order by seed. 24 formal calls plus one excluded RAW
  warmup. No GUI input, click, provider/cloud call, tuning, or retry.
- Pinned runner/auditor image:
  `python@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`
  (`linux/arm64`). Docker bridge reaches the host-local Ollama service; this is
  not network-egress isolation.

## D

`PASS_NORMALIZED_COORDINATE_SIGNAL_SCOPED` only if all 12 pairs and bindings
validate; NORM01 outputs are within `[0,1]` in at least 10/12 pairs; its
exact-target and Engine-hit counts are each at least PIXEL; standard median
source-pixel center error is at most 80% of PIXEL; and it wins pairwise error
in at least 8/12 pairs. Otherwise retain `HOLD_NO_PREREGISTERED_GAIN` or typed
integrity STOP. No threshold changes or retries.

## C

Source image bytes, target geometry/semantics, model digest, temperature,
sampler seed, output keys, scorer, and source-frame mapping are fixed. Only
coordinate units and their interpretation are varied. Arm order is balanced;
requests are sequential, so residual backend-load effects remain possible.

## U

One local model/host, twelve fresh seeds, one public generator family, static
deterministic raster rather than a Tk screenshot. This does not test target
motion, GUI capture, motor/action success, realtime latency, full B0/C1 task
effect, held-out compositions, or cross-domain transfer.
