# Retrospective delivery for #3711 — CLI report persistence p4n7

This publishes the already executed local allocation `cli_report_persistence_p4n7_v1`. It is **retrospective evidence, not GitHub preregistration**. No scientific case is rerun.

Retained disposition: **PASS_LOCAL_CLI_REPORT_PERSISTENCE_BOUNDARY**. Sixteen fresh Tk/X11 cases separated native execution, application text effect, report persistence and read-only recovery. The same CLI exit code 2 occurred after a correct text effect, after native delivery with no text effect, and before API invocation. Missing/invalid retained reports remained non-replayable.

`REPORT.md` preserves the original report verbatim, including its then-true statement that GitHub writes were unavailable. `DELIVERY_VALIDATION.json` is a compact publication copy; the complete original per-control records are inside the capsule.

## Lossless evidence capsule

`capsule/` reconstructs a deterministic tar.xz containing **624/625 original study files**: source, plans/freezes, all formal/construction rows, requests/reports/temp records, stdout/stderr, event journals, PNGs, audits, controls, manifests and process receipts. The only omitted member is the 173181-byte portable runtime executable, because its exact SHA-256 and GitHub Actions provenance are already retained and it is reproducible/downloadable from the repository workflow artifact.

Reconstruct:

```sh
python -S -B restore.py
```

Core capsule SHA-256: `4acdf7feec6f3bca6e1116241f37013855c96e1a80d6fed91f616ee5b5bf9dc1` (89168 bytes).  
Original full evidence ZIP SHA-256: `9f9ef47584e2d6de6a264f1482b9ce91bf90e29427d8c7b289afc2d535c1eed4` (522175 bytes).  
Omitted runtime SHA-256: `b7490f97a01991009e72e1b03410ca244cceeabba12103549c1288ef464c5f19`.

This delivery changes publication state only. It does not upgrade the scientific scope, does not claim independent human review, and does not close #3711, #57, #2789 or the global ROADMAP.
