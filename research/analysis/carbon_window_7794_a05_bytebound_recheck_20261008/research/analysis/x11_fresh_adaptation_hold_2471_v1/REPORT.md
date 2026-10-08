# Fresh-family adaptation — HOLD on gate utility

## H/T/D/C/U

- H: adding a bounded fresh-family sample to adaptation can recover held-out fresh classification without accepted false positives.
- T: train on base 160 + old-shift 80 + fresh-family 80; evaluate remaining fresh-family 80 with fixed 354-parameter CNN and target/confidence >=0.75.
- D: source-bound X11 raw frames/manifests; CUDA RTX 3080; held-out fresh frames untouched.
- C: within-family adaptation only; no domain-generalization, arbitrary GUI, token/latency, gameplay, or runtime claim.
- U: accepted false positive is FAIL; zero acceptance is HOLD.

## Result

| metric | result |
|---|---:|
| train rows | 320 |
| fresh held-out rows | 80 |
| accuracy | 91.25% |
| false positives | 0 |
| accept / YIELD / reject | 0 / 80 / 0 |

Accuracy recovered, but the conservative gate produced no local accepts. **HOLD: no local-gating utility demonstrated.** Prior fresh-family/OOD results remain unchanged.
