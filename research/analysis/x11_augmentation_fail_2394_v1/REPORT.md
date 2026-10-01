# Source-bound X11 augmentation attempt — FAIL / no promotion

## H/T/D/C/U

- H: light training-only translation, scale-proxy, and sensor-noise augmentation may improve shift acceptance without introducing false accepts.
- T: retain the previous 160 plain-background training frames and add four augmented copies per frame using small translations and Gaussian noise; evaluate unchanged 160-frame X11 shift set with the same 0.75 accept / 0.25 YIELD thresholds.
- D: 354-parameter CNN, CUDA RTX 3080, source-bound X11 raw-frame manifest; evaluation set was not modified.
- C: no GUI, token, latency, gameplay, or runtime claim. The local classifier has no authority.
- U: any degraded accuracy or accepted false positive is a FAIL; do not promote augmentation based on this run.

## Result

| metric | result |
|---|---:|
| augmented train rows | 800 |
| unchanged shift rows | 160 |
| shift accuracy | 50.0% |
| shift false positives | 0 |
| accepted / YIELD / rejected | 0 / 160 / 0 |
| accepted false / true | 0 / 0 |

Classification degraded from the prior 98.75% shift accuracy to 50.0%, while the gate still accepted nothing. This is **FAIL: augmentation configuration not useful and not promoted**. The prior HOLD result and all earlier X11/O3 results remain unchanged.
