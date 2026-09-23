# Composed X11 OOD gate before local classifier

## H/T/D/C/U

- H: composing a source-bound OOD gate before a local classifier can route a fresh X11 visual family to YIELD without invoking or authorizing the classifier.
- T: train the fixed 354-parameter CNN on 160 base + 80 old-shift frames; use the fixed 99th-percentile pixel-distance threshold; evaluate the independent 160-frame fresh family.
- D: source-bound X11 raw frames and SHA-256 manifests; CUDA RTX 3080.
- C: composition-only fixture result; no semantic correctness, arbitrary GUI, token/latency, gameplay, or runtime claim. OOD and classifier are non-authoritative.
- U: fresh unknowns must YIELD and must not invoke the classifier; any bypass or accepted fresh sample is FAIL.

## Result

| metric | result |
|---|---:|
| fresh rows | 160 |
| OOD YIELD | 160 |
| OOD pass | 0 |
| classifier calls | 0 |
| composed accept | 0 |
| composed final YIELD | 160 |

This demonstrates safe routing for this fresh fixture only. It does not promote the gate into runtime.
