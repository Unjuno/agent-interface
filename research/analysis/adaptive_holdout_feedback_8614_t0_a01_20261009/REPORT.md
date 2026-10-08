# Issue #8614 T0 A01 — adaptive holdout feedback

## Disposition

`PASS_ADAPTIVE_FEEDBACK_METHOD_SCOPED`. The frozen CPython candidate and independent raw-only auditor each ran once. Candidate receipt: `exec-8392c27a-e15e-4e0f-8604-d19cb73874ea` (exit 0, 10,525 ms); auditor receipt: `exec-84e53525-52cd-4565-8c0c-f1c22e940f70` (exit 0, 749 ms). Exact start/end UTC timestamps were not retained and are unavailable; no times are inferred. The auditor independently reconstructed all 13,312 rows across 512 null and 512 planted replicates, with zero errors; the over-budget proposal was rejected before creating another candidate.

At 16 adaptive rounds in the null family, median selected-winner optimism was 0.02585 for FULL_RELEASE, 0.02753 for AGGREGATE_RELEASE, and 0.00701 for REUSABLE_HOLDOUT. Corresponding false-superiority rates were 72.5%, 76.6%, and 21.7%. The one-query median optimism was −0.00011 for every arm, so the full-release criterion increased with rounds. The bounded reusable policy reduced the 16-query median optimism by 72.9% relative to full release and 74.5% relative to aggregate release.

In the planted-effect family at 16 rounds, discovery power was 100% for FULL_RELEASE and 95.3% for REUSABLE_HOLDOUT, a 4.7 percentage-point difference within the frozen 10-point bound. The separate one-shot null lockbox 95% interval coverage was 94.1%. Every arm preserved exact zero unsafe-attempt, gate-regression, and integrity-failure counts.

## Interpretation and limits

This supports the frozen synthetic method hypothesis: bounded noisy feedback reduced selection optimism and false-superiority declarations while retaining the preregistered planted-effect power in this simulator. Aggregate-only release did not remove the observed selection optimism. The result does not show that any existing Agent Interface benchmark or repository conclusion is biased. The selector, candidate family, outcome distribution, feedback code, Gaussian noise scale, and clipping bounds are synthetic design choices. The noise mechanism is privacy-inspired and bounded; it is not calibrated to a formal differential-privacy guarantee. Exact safety outcomes remained separate and unnoised.

A channel-separated construction audit on disjoint seeds first passed 3,328 rows; its result is construction-only. The formal allocation itself was frozen on current-main `771e8696b66deb18b4b3baf14e1ab8e2bc537edf` before execution. Runtime: CPython 3.14.5, macOS 27.0 ARM64. No model, GUI, API, or live environment was used.

## Reproduction and custody

The exact candidate JSON byte stream is retained as `raw/candidate.json.gz` using deterministic gzip framing. Its decompressed SHA-256 is recorded in `SHA256SUMS`; this is a lossless storage transformation after the one candidate invocation. `REPRODUCE.md` gives decompression, hash verification, and the frozen auditor command. `FREEZE.json` records the preregistered source, seeds, gates, runtime, and pre-run input/source hashes.
