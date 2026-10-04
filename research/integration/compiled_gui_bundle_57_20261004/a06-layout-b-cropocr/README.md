# #57 layout-B crop/OCR adapter diagnostic

This versioned adapter preserves the historical layout-A crop and adds a separately pinned layout-B crop for the integrated-form task path. Layout B crops `(495, 541, 803, 577)`, converts to grayscale, and resizes to `1848 x 216` with Lanczos. Both paths use Tesseract PSM 7 and the frozen alphanumeric/hyphen whitelist. OCR errors become `unknown`; the compiled graph submits only when OCR output exactly equals the task token.

## Evidence and limits

`RESULTS.json` records the audit of six retained screenshots from the engineering-only `integrated-efficiency-live-orchestration-probe-02` run. The image hashes are pinned in `audit_saved_frames.py`: three filled frames returned their exact expected tokens and three blank frames returned `""`, `"ee"`, and `"ee"`; none matched the expected token or a token-shaped pattern. This is a crop-fit check on those frames, not a live GUI result, cold-start caller result, repair/reuse result, or matched A/B/C/D comparison. It earns no formal comparison credit and must not be pooled with #56 or used to change #57's STOP/HOLD decision.

The local environment did not have Docker Desktop available. The audit used extracted Tesseract 5.5.0 and Leptonica 1.84.1 binaries, but their other linked libraries came from Ubuntu 24.04. Pillow 12.3.0 was used; the frozen image's Pillow version is unverified. Therefore this does not establish exact frozen-container equivalence. No provider/model allocation or live GUI task was run.

## Checks

From the repository root:

```powershell
python -B research/integration/compiled_gui_bundle_57_20261004/a06-layout-b-cropocr/test_adapter.py -v
python -O -B research/integration/compiled_gui_bundle_57_20261004/a06-layout-b-cropocr/test_adapter.py -v
python -B -m unittest runtime.core_v1.test_compiled_gui
```

The saved-frame auditor can be rerun with the frozen Tesseract/Leptonica runtime on `PATH`:

```powershell
python -B research/integration/compiled_gui_bundle_57_20261004/a06-layout-b-cropocr/audit_saved_frames.py
```
