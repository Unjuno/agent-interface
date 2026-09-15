# Evidence retention boundary

Complete local archive SHA-256: `b3ac82471309fd84cd7bff00e55f5cc45c323ce0792768a6771bf4cc06566726`.

The local archive contains exact runner, raw JSONL, Xvfb/XTerm logs, Git fixture, manifest, audit result, report and summary. This GitHub branch retains report, summary and audit source only; it is not byte-complete raw retention. Exact runner hash is in SUMMARY.json.

Offline audit after extracting the complete archive:

```bash
python audit.py run-a1
```

No font files are included.
