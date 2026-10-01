# GTK formal source bundle successor freeze (#2796)

This additive successor bundle freezes the exact current-main source closure needed by the #2606
formal matrix runner. It is a small manifest, not a copied runtime tree: every
entry is a repository-relative path plus its SHA-256 at freeze time. The audit
resolves Python local and relative imports transitively and fails on missing or
unlisted repository modules.

Scope is source completeness/provenance only. It does not claim GTK effects,
authority, cleanup, or formal #2606 acceptance. The formal allocation remains a
separate bounded Docker run using the already frozen local GTK fixture image.

Run offline:

```text
python research/integration/gtk_formal_source_bundle_2796_v2/audit.py
```

## Local Docker result

Using pinned `python:3.12-slim-bookworm@sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a` with
`--network none`, the current-main closure froze successfully:

```json
{"bytes":100887,"files":15,"status":"PASS_SOURCE_BUNDLE_FREEZE"}
```

This is a provenance/closure PASS only. It does not claim GTK effects,
authority, cleanup, or formal #2606 acceptance.

