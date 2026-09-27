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
- The full 4.17 MB raw output is retained locally at `work/formal_tiny_visual_equivariant_4814_v1/` and compressed into `work/formal_tiny_visual_equivariant_4814_v1.zip` (847,667 bytes, SHA-256 `4edc2022cd1b911a57f702c3d3ccbb7208c42afc90721dd40001986197fd81c7`). The archive was expanded and byte-checked (16 files, 4,168,206 bytes); the predictions digest reproduced exactly. GitHub MCP contents uploads are text-only and local `gh` has no authentication in this workspace, so the archive remains local pending an authorized binary artifact upload mechanism.
- The initial audit mistake and its correction are recorded in `FAILED_FIRST_AUDIT.json` and `STOP.json`; the original output directory was never rerun or overwritten.

## Formal seed results

| Seed | CNN base positive ACCEPT | CNN heldout positive ACCEPT | MLP heldout positive ACCEPT |
|---:|---:|---:|---:|
| 8963800 | 0/40 | 0/320 | 40/320 |
| 8963900 | 0/40 | 0/320 | 40/320 |
| 8964000 | 0/40 | 0/320 | 40/320 |
| 8964100 | 0/40 | 0/320 | 40/320 |
| 8964200 | 0/40 | 0/320 | 40/320 |

## Key file digests

- `predictions.jsonl`: `1b0d1dbb713a80eed9ca3b4d52fb41ea8cf22afb20ad59af82edc286597dd205`
- `training_manifest.jsonl`: `d49ed8e0b6e0ca35679067bba811adb45398e1304416a480d9d31062cc6829ac`
- `evaluation_manifest.jsonl`: `5b32b4f3eae28f56123e40977a23b3d0e614e4f7dc9448e9ad11953b12f46987`
- `training_receipts.jsonl`: `d8f2d4eb86833be7849e8b0d288f6d2f0401a21b71715aeefa17982d5c31a043`
- `environment.json`: `1a126506542d6e818f5daaecc49f75ed3ff311f11108482f2ebe5d61bb7d4726`

