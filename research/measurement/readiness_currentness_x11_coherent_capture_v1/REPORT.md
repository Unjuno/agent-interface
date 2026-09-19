# #1464 first formal outcome

Decision: **PASS_READINESS_CURRENTNESS_X11_COHERENT_CAPTURE_SCOPED**. Formal invocation 1; reruns/replacements/tuning 0.

## Result

- coherent rows: 3200 / split rows: 3200
- coherent candidate/oracle mismatch: 0
- mixed-epoch race: coherent false effects 0/800; split discriminator false effects 800/800
- stable VALID+READY: coherent effects 800/800
- HARD+READY: coherent effects 0/800
- VALID+NONREADY: coherent effects 0/800
- generation decode unknown: 0
- coherent XGetImage+decode p50/p95/p99/max: 0.087459/0.141399/0.235499/1.065717 ms
- directed controls: 8/8
- authority/task-input actions: 0/0

Independent audit: **PASS**, errors []. Frozen source rehash exact 4/4.

Raw first-outcome JSON: 1,400,892 bytes, SHA-256 `48201c7f2c03ff9b4a5c4ff13c48345acd3bef66526f85c2be98189884ae6756`. Deterministic gzip: 123,473 bytes, SHA-256 `4a5d6fe415723ea6660ad19b59736ed2bd6f9a721fac6cec54e00e2b7718ca20`. The connector publication retains the audited summary/hash commitments rather than duplicating the 1.4 MB row ledger; no rerun or summary substitution occurred.

## Scoped interpretation

On this private Xvfb/Tk fixture, deriving currentness, readiness, and readiness generation from one XGetImage payload preserves the final guard and prevents the deliberately exposed mixed-epoch admission race. Two independently timed ROI reads can synthesize `VALID + READY` even though neither actual fixture state was admissible. This is a pixel-source coherence transfer only, not a universal cross-modal transaction or production ABI result.

## Next discriminator

A distinct successor may combine this pixel evidence with one independently timed non-pixel critical field (for example focus or surface identity) under the #42 observation-epoch contract. Do not infer that one XGetImage synchronizes non-pixel modalities.
