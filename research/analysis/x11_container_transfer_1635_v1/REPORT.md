# X11 container transfer preflight — Issue #1635

## H/T/D/C/U

- H: a disposable Xvfb + Tk + python-xlib fixture can provide source-bound native X11 pixel bytes and train a bounded local classifier on this machine.
- T: build a Python 3.11 Debian container, install Xvfb/Tk/python-xlib, collect 120 alternating target/no-target frames at 320×240, persist raw X11 bytes and SHA-256 receipts, then train the fixed 354-parameter CNN on an 80/40 split.
- D: container image `codex-x11-preflight:local`; every frame was captured through Xlib `get_image`; manifest records generation, dimensions, byte count, label, and SHA-256.
- C: this is a container/X11 fixture result only. It does not claim DOOM gameplay, arbitrary GUI transfer, latency, token savings, or runtime promotion.
- U: any missing or mismatched receipt is a stop condition; future work must add independent audit and stronger occlusion/temporal cases before broader transfer claims.

## Result

| metric | result |
|---|---:|
| frames | 120 |
| frame bytes | 307,200 |
| unique SHA-256 hashes | 61 |
| model parameters | 354 |
| device | NVIDIA RTX 3080 Laptop GPU / CUDA |
| held-out test accuracy | 1.0 (40/40) |
| held-out false positives | 0 |

The initial Dockerfile had a syntax error, and the first runtime image exposed that Debian's `python3-xlib` was not visible to the `/usr/local` Python interpreter. Both were fixed before the formal run. The final build and collection completed successfully.
