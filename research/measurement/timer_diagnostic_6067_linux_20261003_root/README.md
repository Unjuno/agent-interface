# Linux timer diagnostic construction for #6067

Read [REPORT.md](REPORT.md), then [PLAN.md](PLAN.md) and [RUN.md](RUN.md). `output/run-d02/raw.jsonl` is the unchanged first successful construction output; `audit-v2.json` is a saved-only arithmetic reconstruction, not a live/scientific rerun. D01 STOP is retained.

Saved-data checks (never execute candidate for evidence verification):

```sh
sha256sum -c SHA256SUMS
python auditor_v2.py output/run-d02 /tmp/timer-6067-audit.json
```

Container receipts are allowlisted public copies. Original complete inspections are retained privately by the execution worker with SHA-256 identity; proxy environment/host mount internals are omitted from publication. No runtime imports, automated formal execution or CI workflow is introduced. Candidate requires an explicitly supplied new output path and is not test-discoverable.

Integration decision: instrumentation reference only; HOLD capture policy/runtime adoption. Linux measurements neither identify the previous macOS STOP cause nor qualify a next native allocation. #6067/#57/#59 stay open.
