# Issue #1998 A05: retained Inkscape task-marker crop

This package tests whether any of the already-frozen A04 crops for one retained
Inkscape final frame preserve the four geometry values shown in the selection
toolbar, as read by the fixed Tesseract OCR executable. The saved SVG in the
same retained task run is the geometry oracle. It makes no claim about a vision
model, human readability, crop proposal quality, live GUI behavior, or task
success.

The allocation is one-shot. `FREEZE.json` and `FREEZE.sha256` bind the frame,
saved SVG/result, all 20 smaller A04 crop artifacts, OCR executable and English
traineddata, and candidate/auditor source. Formal candidate output and audit
are retained under `results/`. A04's own candidate/auditor output is an input;
neither is rerun.
