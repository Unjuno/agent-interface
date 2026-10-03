# G21 grayscale plus PSM consensus diagnostic

This is a bounded follow-up to G20's rejected thresholded PSM7 OCR route. It tests one different candidate: unthresholded grayscale cells, nearest-neighbor 4x scaling, and unanimity across fixed Tesseract PSM modes 6/7/8/10/13 with abstention on disagreement. G12's one-crop PSM comparison already established that the five modes can agree on one known image; this run applies that predeclared refusal rule to the full eleven-frame G20 corpus.

The diagnostic reuses known G08-G12 frames from G20 and is not held out. Duplicate source hashes are repeated frame evidence, not independent samples. The ground-truth sidecar is separate from `input/` and the candidate code does not load it. Five modes from one Tesseract build are correlated outputs, not independent votes.

See `FREEZE.md` for the exact preregistered candidate and decision rule. `ENVIRONMENT.txt` records the OrbStack image-store error before the local run. `candidate.py` writes raw calls exactly once; `audit.py` independently checks raw custody and scores only after candidate completion. No GUI, model, native input, previous allocation replay, or runtime change is included.

Disposition and audit status are recorded in `REPORT.md` and `AUDIT.json`. These results only inform the known-image OCR blocker and do not establish held-out accuracy, a safe runtime recognition strategy, task effects, or end-to-end efficiency.
