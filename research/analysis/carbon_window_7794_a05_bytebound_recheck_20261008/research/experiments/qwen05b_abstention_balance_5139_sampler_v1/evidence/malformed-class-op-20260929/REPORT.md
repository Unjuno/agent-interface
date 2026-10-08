# Malformed class-operation auditor robustness

Date: 2026-09-29 (Asia/Tokyo)

## H / T / D / C / U

- **H — Hypothesis:** the independent class derivation in `audit_results.py` must fail closed on every JSON-representable malformed `intent.op`; a list/object value must not crash the auditor.
- **T — Test:** synthetic sentinels formal `830513911`, support `830513912`; changed `support_pool[0].intent.op` to `[]` and `heldout_pool[0].intent.op` to `{"malformed": true}`. Same serialized input was exercised before and after the guard. No model, GPU, CUDA, Docker, GUI, or formal allocation was used.
- **D — Data:** pre-fix run raised `TypeError: unhashable type: 'list'` while deriving the class. Post-fix run returned `integrity_pass=false`, `raised=null`, and explicit `support_class_mismatch:support-0000` plus `heldout_class_mismatch:heldout-0000`. The altered canonical input SHA-256 is `7c6ff7f2d19e2f80dc3950345d3a30a3ba1b590af8b2cf6a0088ba937206d3bf`; post-fix output is `result.json`. The first script launch omitted the package directory from Python's import path and stopped with ModuleNotFoundError; this setup failure is preserved in `launcher-stop.json`. Rerunning the same script with `PYTHONPATH=.` reached the test.
- **C — Conclusion:** guard non-string `op` before reason-map membership. Auditor now returns structured rejection rather than throwing on list/object operation tags. Regression covers both unhashable JSON types. Full package suite: **29/29 passed**; `git diff --check` clean. The reproduction call intentionally supplied no raw arms, so `missing_raw:*` errors are expected and unrelated; acceptance is assessed by the two explicit class-mismatch errors and no exception.
- **U — Limits / next step:** one synthetic input on Windows CPython 3.11 and one targeted mutation family. This does not establish full JSON-depth/size robustness, all malformed intent schemas, raw-arm integrity, model quality, or GPU behavior. Keep PR #5208 Draft pending independent review and #5139's source/provenance/resource gates. No GPU/Docker lease is evidenced; do not launch the local model or container.

## Reproduction

From this package directory:

```powershell
$env:PYTHONPATH='.'
python evidence/malformed-class-op-20260929/reproduce.py
python -m unittest discover -s . -p 'test_*.py' -q
```

This is a synthetic audit-robustness check attached to #5139, not a Qwen experiment result.
