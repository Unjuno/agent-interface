# Source-bound X11 local model distribution-shift gate

## H/T/D/C/U

- H: a 354-parameter local CNN trained on source-bound X11 frames can accept clearly known observations while yielding shifted or uncertain observations.
- T: Docker-generated 160 training frames (48px target, plain background) and 160 held-out shift frames (20/28/36/60/72px target sizes, random position, clutter, and periodic occlusion). Train only on the first split; evaluate the second split with accept >=0.75, YIELD [0.25,0.75), reject <0.25.
- D: raw X11 XGetImage bytes, SHA-256 manifest, CUDA training on the local RTX 3080, fixed 354-parameter CNN.
- C: fixture-only result; no arbitrary GUI, token, latency, gameplay, or runtime authority claim. The local model is not authoritative; YIELD is the safe outcome.
- U: HOLD if no shifted sample is safely accepted; FAIL on accepted false positives; continue only with a separate successor using calibration or augmentation.

## Result

| metric | result |
|---|---:|
| train / shift frames | 160 / 160 |
| model / device | 354 parameters / CUDA RTX 3080 |
| shift accuracy | 98.75% |
| shift false positives | 0 |
| accepted / YIELD / rejected | 0 / 160 / 0 |
| accepted false / true | 0 / 0 |

Classification remained accurate, but confidence was insufficient for the conservative accept threshold on every shifted frame. Therefore this run is **HOLD: safety preserved, no suppression value demonstrated**. The prior X11/O3 results remain unchanged.
