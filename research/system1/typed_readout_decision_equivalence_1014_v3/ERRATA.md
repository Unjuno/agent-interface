# Source-hash erratum

The merged #4639 README declares corpus SHA-256
`c70d4ba3d06dec161fdc8d3f5e5312fbe3ff0af1c1a36cdcb0dc0e290efe27fd`. On the
current main, the predecessor `SOURCE_MANIFEST.json` lists the bytes of
`corpus.jsonl` as `85b5bee5d5a69dab1ff0d094cdbad70d4cd66fcff505b36667978817ed30a49c`,
and direct local SHA-256 independently returns the same value. This successor
pins the directly verified file bytes as `85b5...` and records both Issues'
comments. The #4639 raw construction/audit files remain unchanged; their
per-prefix hashes are consistent with these corpus rows. This is a metadata
correction only and does not revise either scientific outcome.
