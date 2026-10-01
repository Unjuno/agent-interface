# Pre-run stops (not scored; no model initialization or case execution)

Two disposable container starts exited during source preflight before reading model weights:

1. The first start mounted model and engine but did not mount the frozen source directory; preflight stopped because `/opt/experiment/Dockerfile` was missing.
2. After mounting source read-only, preflight found a one-character transcription error in the preregistered `PREREGISTRATION.md` SHA-256 in `FREEZE.json`. The actual source SHA-256 was `44bfd854b6130a582fea2122df1e59c2c3f522d9e72c7ccf31da8ec02b76f685`; the corrected manifest was committed before the scored run.

The corrected source manifest was verified in a separate network-isolated construction diagnostic: all six listed source hashes matched exactly. The scored run then initialized the model and executed all seven frozen cases once. No prompts, cases, or model weights were changed.
