# Successor #4752: tiny spatially shared CNN

Status: FAIL (efficacy); first audit HOLD was retained separately. The corrected independent audit reproduces all 10 fits and 7,200 predictions from the frozen inputs and weights.

## Question

Does a 45-parameter shared 3x3 convolution + global spatial max-pooling model generalize positive visual patches to unseen positions better than the parent's 19,233-stored-value MLP under the same paired synthetic data, 250 full-batch gradient steps, and local CPU container?

## Formal result

- 5 paired seeds; 10 total local fits; 3,200 heldout examples per arm (1,600 positive, 1,600 negative), plus 400 base-position examples per arm.
- CNN heldout ACCEPT: 0/1,600 positives, every one of 8 locations 0/200. MLP heldout ACCEPT: 200/1,600 (12.5%), concentrated entirely at one center; it achieved 0 elsewhere.
- CNN base-position ACCEPT: 0/200 positives. Heldout false ACCEPT: 0/1,600. CNN-minus-MLP heldout ACCEPT difference: -12.5 percentage points.
- CNN accuracy by heldout location was 0.58, 0.5725, 0.56, 0.5525, 0.56, 0.3125, 0.58, 0.5375. These are diagnostic only; acceptance gate failed.
- All stale/digest/negative fixtures rejected, but this does not rescue efficacy.
- Local Docker image `sha256:ba509e8a38d311c07539c49a7a2970b6f19869de42b8008be07a85568e2c9824`; no network/GPU/external API; 19.64 s training wall, 19.18 s summed fit, 0.0221 ms/row warm p95.
- Independent audit file SHA-256: `3a77dfcdc95528d1ee951708d5ba3b0bbabd0923c448adb814abe9cf9f794cbe`.

## Interpretation and limits

The result does not support adopting this CNN. It did not meet even the base-position competence gate; probabilities remain around the decision boundary, consistent with failure to optimize within the inherited 250-step recipe. Thus this is not a clean test of translation equivariance in an otherwise competent CNN. The MLP comparator's 12.5% aggregate rate is itself position-specific (200/200 at one location and 0/200 at seven); the previous #4752 estimate used a different target/data schedule and must not be treated as an identical comparator. No real UI, pixels, GUI authority, or deployment behavior was tested.

Next: a new successor should first demonstrate train/base competence on a construction-only split, validate convolution gradients against finite differences, and freeze a training schedule selected without formal seeds. It should report per-position and pooled outcomes against a paired MLP with identical data and initialization protocol. Preserve this failed formal allocation unchanged.

## Provenance

- Source, frozen recipes, initial audit HOLD, corrected audit, and evidence manifest are adjacent in this directory.
- Formal seed allocation: `tiny-visual-equivariant-cnn-2564-20260927-01`.
- Formal output bundle manifest: `MANIFEST.json` (all raw files and byte-level SHA-256 digests).
- The full 4.17 MB raw output is retained locally at `work/formal_tiny_visual_equivariant_4814_v1/` and is not duplicated into the source branch; `MANIFEST.json` identifies all bytes. Per-row data and weights can be attached in a later artifact commit if needed.
- The initial audit mistake and its correction are recorded in `FAILED_FIRST_AUDIT.json` and `STOP.json`; the original output directory was never rerun or overwritten.

