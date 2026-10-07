# G12 diagnostic auditor hardening successor

This additive successor addresses two review findings for the retained
`calc_g12_tesseract_psm_diagnostic_20261004` package without changing its
`RAW.json`, `AUDIT.json`, original auditor, runner, crop, or checksums.

`audit_raw_v2.py` is read-only by default: it recomputes and prints the scoped
report. `--compare-retained` compares that report with the preserved audit.
Only an explicit `--write-audit PATH` requests output, and exclusive creation
refuses to replace any existing path. The verifier binds every argv position
except the intentionally varying PSM value, including the executable path,
input, output selector, language, and whitelist.

Run the retained-only tests with:

```sh
python3 -m unittest discover -s research/integration/calc_g12_tesseract_psm_diagnostic_review_v1 -v
```

The tests do not invoke Tesseract. They compare against retained bytes and
mutated scratch records only. This remains a known-image diagnostic, not an OCR
regrade or held-out accuracy result.
