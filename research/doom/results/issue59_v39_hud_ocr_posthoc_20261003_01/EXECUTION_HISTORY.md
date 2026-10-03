# Execution history qualification

The preceding work segment ran the 14-frame OCR matrix once informally and
three times through successive packaging revisions. The three packaged runs
each reported the same fixed-configuration counts: grayscale PSM 7/8/10/13
matched 2/4/1/4 of 14, and all eight threshold configurations matched zero.
The final packaged execution began at 2026-10-03T08:42:35.208354Z and its full
per-call output/timing is the retained `RESULT.json`.

Earlier packaged runs wrote the same output filename. Their full raw text and
timing files were overwritten; only their tool-returned aggregate counts are
available in the conversation. This is a preservation limitation. The retained
result must not be represented as a one-shot preregistered experiment, an
independent replicate, or a complete archive of all earlier raw outputs.

The original four hash-bound source files and final RESULT are preserved as
recorded. `experiment.py` writes RESULT in place, so any future reproduction
must use a separate copied checkout/output. The distinct color-channel study
uses exclusive-create output files and separately named calibration/evaluation
records to avoid this loss.
