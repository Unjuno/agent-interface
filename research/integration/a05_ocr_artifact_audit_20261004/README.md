# Independent retained-artifact audit for the A05 OCR diagnostic

This read-only check independently joins PR #7628's offline OCR record to the retained A05 source screenshots, derived crop previews, archived OCR-input PNGs, and historical failure diagnostics. It pins all inputs by Git commit and SHA-256. It runs no GUI, model, study runner, or formal allocation.

Run from the repository root after fetching the referenced Git objects:

```powershell
git fetch origin main
git fetch origin refs/pull/7628/head:refs/remotes/origin/pr/7628
python -B research/integration/a05_ocr_artifact_audit_20261004/audit.py
```

The auditor pins PR #7628's recorded result commit `473c913c2a0baa0acebd11539c9be5eaffbdc97b`, the audited main snapshot `d6a3fe646d6a8ea92a8688a1f7c54b89261f56f6`, and source screenshots at `58bcbb4c45501880db8782158ddd3add3b765984`. The generated `AUDIT.json` records the exact result.

## Result and limits

The retained-source and derived-artifact linkages pass: three source screenshot hashes, six crop-preview hashes, the crop manifest digest, three archived OCR-input PNG hashes, six recorded OCR rows, and three historical diagnostic rows are internally consistent. The current terminal does not have Tesseract on `PATH`, so the claimed Tesseract 5.5.2 OCR results were not rerun here. The audit does not qualify the original online observer or historical OCR environment.

The three “near miss” rows substitute a different expected task token and apply strict string equality; they verify rejection by the comparison predicate, but do not perturb image pixels or measure OCR false acceptance. The frozen source commit pins the source screenshots, while the later crop manifest/previews are identified by SHA-256 on the audited main snapshot.

This result verifies retained evidence identity and record consistency only. It does not change the historical A05 9/12 C-arm outcome, the #57 HOLD decision, or any live-allocation gate.
