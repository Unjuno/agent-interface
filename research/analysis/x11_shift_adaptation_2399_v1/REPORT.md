# Source-bound X11 shift adaptation — bounded held-out result

## H/T/D/C/U

- H: exposing a bounded sample of source-bound shift frames to local adaptation can improve conservative gate utility on a disjoint remainder without accepted false positives.
- T: keep 160 base training frames; add the first 80 shift frames to training; evaluate only the remaining 80 shift frames. Use the unchanged 354-parameter CNN and thresholds accept >=0.75, YIELD [0.25,0.75), reject <0.25.
- D: raw X11 frames and SHA-256 manifest from the prior container run; CUDA RTX 3080; deterministic split and seed.
- C: bounded adaptation evidence, not domain-generalization, arbitrary GUI transfer, token/latency benefit, gameplay, or runtime authority.
- U: any accepted false positive is FAIL; a fresh shift family is required before promotion.

## Result

| metric | result |
|---|---:|
| base / adaptation / held-out shift | 160 / 80 / 80 |
| shift held-out accuracy | 88.75% |
| false positives | 0 |
| accept / YIELD / reject | 56 / 24 / 0 |
| accepted false / true | 0 / 16 |

This improves gate utility relative to the previous 0/160 acceptance HOLD, but the adaptation sample comes from the same generated shift family. It is a bounded positive result, not a promotion or generalization claim. A fresh shift family remains required.
