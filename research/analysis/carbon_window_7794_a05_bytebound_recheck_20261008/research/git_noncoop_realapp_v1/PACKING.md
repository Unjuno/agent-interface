# Evidence retention boundary

Complete local archive SHA-256:

`d9185cd370f394ffb8ccefcb24e6192239e6c705bab9ad0f02bbfbba58e736dc`

The local archive contains exact runner source, raw JSONL, terminal screenshots, Xvfb/XTerm logs, manifest, audit result, report and summary.

This GitHub branch retains report, summary and independent audit source. **The complete binary raw archive and exact runner are not stored in this PR.** Exact source hashes are in SUMMARY.json; the branch is not byte-complete raw retention.

Offline complete-archive audit:

```bash
python audit.py run-a1
```

No font files are included.
