# Source-bound GUI frame capture — stop record

Date: 2026-09-19 (Asia/Tokyo)

## H — Hypothesis

The local machine can provide a source-bound GUI frame that could eventually replace the synthetic raster inputs used by the tiny local relevance model.

## T — Test

- Host: Windows 11, Intel i7-12700H, 31.7 GB RAM, RTX 3080 Laptop GPU.
- Source window: Docker Desktop, title `Containers - Docker Desktop`.
- Observation method: computer-use window-state capture.
- Two independent observations were requested, including screenshot and accessibility text.

## D — Data

- Both observations returned a fresh screenshot for the exact Docker Desktop window handle.
- The accessibility text field was `null`.
- No pixels were decoded, saved, uploaded, or used as training data.

## C — Conclusion

The source-bound capture path is viable, but this run did not produce a machine-readable frame/label contract. It therefore cannot validate the local model or support a source-bound accuracy claim. The result is a preflight success followed by a data-contract stop.

## U — Next action

Keep the synthetic-only MLP result bounded to its existing claim. Resume only after a controlled fixture provides repeatable pixels plus labels/receipts (or an equivalent non-GUI observation contract). Prefer a disposable container or X11 fixture; do not use an uncontrolled desktop screenshot as a training set.
