# Evidence retention boundary

Complete local evidence archive SHA-256:

`a1bf6aa40c35773a181935888d3675c8f3fce910d373c7303a188b389852cce6`

The local archive contains setup/harness/time-limit directories a1–a5, completed a6, Rung-2 provenance allocation, 600-row primitive benchmark, exact runner sources, manifests, logs, XTerm screenshot, audit outputs, report and summary.

This GitHub branch retains the readable report, failure ledger, summary and independent audit source. **It does not store the complete binary evidence archive or exact runner sources.** Exact runner hashes are in SUMMARY.json. Therefore the branch is not byte-complete raw retention.

Offline complete-archive audit:

```bash
python audit_all.py .
```

No font files are included.
