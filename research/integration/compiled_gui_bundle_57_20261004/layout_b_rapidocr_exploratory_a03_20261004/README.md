# Layout-B RapidOCR exploratory replay A03

**Disposition: EXPLORATORY ONLY; not a qualification result.** This is a retrospective native macOS CPU replay of screenshots already inspected under A02. It cannot qualify layout B or support an efficiency claim.

The A02 ImageMagick crop, alpha removal, grayscale conversion, 800% scale, and 32 px white border were held fixed. RapidOCR 3.9.2 used ONNX Runtime CPU 1.30.0 defaults with PP-OCRv6 small detection/recognition and the PP-OCR mobile orientation classifier. No custom vocabulary, character whitelist, postprocessing, or fuzzy matching was used. Detected text segments were concatenated in returned order and only outer whitespace was stripped before exact comparison. The run processed all 56 A02 plain/persistent task-4–6 images once. `RAW.json` preserves source/crop hashes, raw recognized segments, exact comparisons, and per-image engine time. The model file hashes are included.

RapidOCR exact matches cover task 5 and task 6 in both arms; task 4 is still missed (`t991028-4` is read as `1991028-4`). A02 Tesseract has exact positives only for task 4 in each arm. Thus their retrospective union has at least one exact image for all six task/arm cases, and neither engine yields an exact source-frame positive among the 56 frames. This union only covers the fixed token set in A02. A later targeted transfer replay on r02 task-4 new tokens found RapidOCR also misread both leading `t` characters, so the union is not a reliable general route. See sibling `layout_b_vision_r02_transfer_a04_20261004/` for a separate macOS-only diagnostic. In the retained journal, persistent-arm RapidOCR positives on frames 110 (task 5) and 133 (task 6) have capture timestamps before their POST records; the plain-arm saved frame sequence has no matching capture timestamp in its journal, so pre-POST timing for its positives is unverified.

The measured batch elapsed time was 30.254458 s for 56 images, including crop creation and inference but excluding RapidOCR/model initialization and audit. RapidOCR reported 5.462063 s summed per-image engine time. Neither is end-to-end task latency. The work ran natively on Darwin ARM64 because the local container runtime was unavailable. It did not connect to a GUI or emit input.

For a fresh prospective qualification, freeze a dual-engine exact-only decision rule before a new task run, test unseen random tokens in both layouts, require exact negatives before typing and exact positives before submission, and count both engines' setup and scan cost. Any mismatch must safely yield. Do not use this retrospective union as a PASS or modify the A02 disposition.

## Reproduction

Use Python 3.14 on macOS ARM64 or a compatible CPU host:

From the repository root:

```sh
python3 -m venv work/rapidocr-a03-venv
work/rapidocr-a03-venv/bin/python -m pip install -r research/integration/compiled_gui_bundle_57_20261004/layout_b_rapidocr_exploratory_a03_20261004/requirements.txt
work/rapidocr-a03-venv/bin/python research/integration/compiled_gui_bundle_57_20261004/layout_b_rapidocr_exploratory_a03_20261004/run_probe.py
work/rapidocr-a03-venv/bin/python research/integration/compiled_gui_bundle_57_20261004/layout_b_rapidocr_exploratory_a03_20261004/audit_probe.py
```

The model package downloads its model files on first initialization. The expected SHA-256 digests are in `RAW.json`. The runner replaces only `RAW.json`; preserve a copy before rerunning if the prior raw is needed.
