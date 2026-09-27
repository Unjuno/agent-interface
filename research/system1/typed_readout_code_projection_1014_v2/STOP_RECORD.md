# STOP record — Issue #4639

**Disposition:** `STOP_SELECTED_CODE_TOLERANCE` during excluded GPU construction.
The preregistered selected-score gate failed, so no formal latency or semantic
block was started. This is a separate successor result; it does not revise the
full-vocabulary STOP in #4623.

## Scope and inputs

- Model: Qwen2.5-0.5B-Instruct, revision
  `7ae557604adf67be50417f59c2c2f167def9a775`; exact model files and license are
  in the predecessor's `MODEL_MANIFEST.json`.
- Corpus: predecessor's immutable 64×16 `corpus.jsonl`, SHA-256
  `c70d4ba3d06dec161fdc8d3f5e5312fbe3ff0af1c1a36cdcb0dc0e290efe27fd`.
- GPU: NVIDIA GeForce RTX 3080 Laptop GPU, CUDA 12.1; exact container image and
  dependency versions are in the predecessor's manifests.
- Observable: eight answer-code logits, token IDs 15–22; full-vocabulary
  scores are outside this successor's gate.
- Frozen gate: same answer argmax and absolute **and** relative selected-score
  error ≤0.002 for every excluded comparison.

## Construction result

Three excluded bundles (B00, B17, B63) and slots 0, 7, 15 were checked. The
token IDs, exact prompt/token concatenation, cache isolation, stale generation,
foreign bundle, changed prefix, and unsupported multi-token controls passed.
All nine answer winners matched. Eight of nine selected score vectors met the
frozen tolerance. B00/slot 15 failed with maximum absolute error `0.078125` and
maximum relative error `0.003223726525902748`. Therefore the construction gate
failed even though no answer winner changed.

The independent audit uses an independent implementation of the full and
incremental model calls. It reconstructed all nine score vectors, revalidated
recorded controls and prefix hashes, reported `PASS_RECONSTRUCTION`, and had
`errors=[]`; its fixed selected-score gate was `FAIL` on the same comparison.
Raw records are `construction/CONSTRUCTION_001.json` and
`construction/AUDIT_CONSTRUCTION_001.json`.

## Stop reason and limits

The frozen gate required every score comparison to pass, not merely unchanged
argmax. A retry, looser tolerance, source change, new model, or post-result
filter would be a different experiment. No formal 1,024-bundle arm, timing,
semantic-quality, #1015 shadow-capability, GUI, or product claim was run.
This result applies only to this pinned model, corpus, image, GPU and selected
answer-code observable. The previous full-vocabulary failure remains intact.

## Reproduction

`construction.py` ran in the network-disabled GPU Docker environment documented
by Issue #4639. `construction_audit.py` independently reran the frozen
comparisons in a separate GPU container against the retained raw record. The
exact invocation, environment, source hashes and audit log are retained in this
package; no model or corpus was rematerialized for the successor.
