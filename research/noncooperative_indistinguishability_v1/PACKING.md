# Evidence retention note

A complete local evidence archive was produced for both frozen allocations.

Whole archive SHA-256:

`b216da40ffabf6d2d5f64f912d413583ec0690ec7ab53d7925380b265eb35471`

It contains raw JSONL, XTEST effect receipts, frames, Xvfb logs, manifests, exact runner sources, imported inherited sources, audit outputs, `SUMMARY.json`, and `REPORT.md`.

The GitHub research branch retains the report, compact summary, and independent audit source. **It does not retain the complete binary raw archive or exact experiment runners.** Their SHA-256 values are recorded in `SUMMARY.json`. Therefore this branch is reviewable evidence, not byte-complete raw retention or a standalone rerunnable package.

The separately retained complete archive can be audited after extraction with:

```bash
python audit.py run-a1
python audit_r2.py run-r2-a1
```

Python bytecode caches are excluded. No font files are included.
