# Evidence retention boundary

Complete local archive SHA-256: `d27b360db35d688e8e3cf1cf7c6dc9080b8a1cf288e7eecd9c5fe235e9fc2244`.

The complete archive contains harness-failure a1, completed XTerm a2, 900-row dependency-set block, exact runners, raw JSONL, Xvfb/XTerm logs, manifests, audits, report and summary.

This GitHub branch retains report, summary and independent audit sources. **The complete binary archive and exact runners are not stored here.** Exact source hashes are in SUMMARY.json; the branch is not byte-complete raw retention.

Offline complete-archive audits:

```bash
python audit.py run-a2
python audit_r2.py run-r2-depsets
```

No font files are included.
