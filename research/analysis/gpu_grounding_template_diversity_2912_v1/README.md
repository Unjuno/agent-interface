# Held-out form-template GPU experiment

Issue #4546 is the canonical question and decision record. This is a new synthetic allocation after the #2912/#4482 six-source-image HOLD; it does not modify or pool any predecessor evidence.

- `templates.json`, `generate_corpus.py`: 12 frozen local synthetic template families and deterministic rasterization.
- `corpus/manifest.json`, `corpus/images/`: 240 unique images, source-template split 8 train / 4 held-out.
- `PREREGISTRATION.md`, `FREEZE.json`: frozen treatment and source hashes before the one formal invocation.
- `train_eval.py`, `audit.py`: local CUDA runner and independent CPU audit.
- `test_construction.py`: no-training model/data/validator/CUDA determinism checks.
- `results/formal01/`: one formal result and audit, when authorized by the completed freeze.

All data is synthetic and raster-generated; it is not evidence of real application or production grounding. Predictions are measured but never acted on. The strict validator proves candidate schema and bounds only.
