# Container fixture training result

Date: 2026-09-19 (Asia/Tokyo)

## H/T/D/C/U

**H** — A local Docker container can generate a repeatable frame/label fixture that is consumable by a small local trainer.

**T** — Used the pre-existing local image `python:3.11-bookworm` with no registry pull. Mounted `work/` into the container and generated 240 32x32 PGM frames plus `labels.csv`; 120 were positive and 120 negative. Host-side NumPy logistic regression trained on the mounted raster files with a deterministic 80/20 split.

**D** — 240 frames; train accuracy 1.00; held-out test accuracy 1.00; test false positives 0.

**C** — Docker generation, host mount, label transport, and local training work end to end. This remains a deliberately separable fixture and does not support GUI, gameplay, or source-bound relevance claims.

**U** — Replace the generator with a disposable X11/container application whose state receipts produce labels. Keep the held-out and distribution-shift gates.
