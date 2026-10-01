# GTK formal source bundle freeze (#2780)

This additive bundle freezes the exact local source closure needed by the #2606
formal matrix runner. It is a small manifest, not a copied runtime tree: every
entry is a repository-relative path plus its SHA-256 at freeze time. The audit
resolves Python local and relative imports transitively and fails on missing or
unlisted repository modules.

Scope is source completeness/provenance only. It does not claim GTK effects,
authority, cleanup, or formal #2606 acceptance. The formal allocation remains a
separate bounded Docker run using the already frozen local GTK fixture image.

Run offline:

```text
python research/integration/gtk_formal_source_bundle_2780_v1/audit.py
```

