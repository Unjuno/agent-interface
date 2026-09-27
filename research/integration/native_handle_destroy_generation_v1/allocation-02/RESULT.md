# Allocation 02 — formal result

**Disposition: `PASS_NATIVE_DESTROY_GENERATION_COMPOSITION_SCOPED`.** This is the scoped result for allocation `native-handle-destroy-generation-20260923-02`; allocation 01 remains the separate immutable `STOP_FIXTURE_PIXEL_CAPTURE_BADMATCH_BEFORE_BRIDGE` (0/12 rows).

## Frozen execution and retained result

- Exact source/head: `5aefa977c1c6839113fa2fc719475a82e5b5a0dc`.
- GitHub Actions run: `35822481502`; formal job completed successfully.
- Exactly one formal invocation, 12 rows across four fresh sessions, zero retries.
- Formal stdout records 12 rows and four sessions. The retained independent raw-only audit reports `PASS_RAW_AUDIT`, `PASS_NATIVE_DESTROY_GENERATION_COMPOSITION_SCOPED`, `errors=[]`, and `failures=[]`.
- Corruption controls report 11/11 rejected. Formal, audit, and controls process exit codes are all 0.
- `SOURCE_SHA256SUMS.txt` was independently checked against the exact source commit: all 15 listed source files match.
- The retained terminal-release records are verified; no allocation 01 result was changed or pooled.

The complete downloaded workflow artifact is retained in this directory. Its artifact ID is `10732979823`; the Actions artifact ZIP SHA-256 from the run log is `039440a8115c1434e11b2bc59ed6f6a07245f3a6727a532913e6e09dfd3b66c9`. Principal extracted-file hashes:

`SHA256SUMS` binds every extracted workflow-artifact file in this directory (excluding the documentation and the manifest itself).

| File | SHA-256 |
|---|---|
| `RAW.json` | `1d1330d7d71659e02a03fe9a4d2de5cbde784f6c5041e181a02fa276343ecadd` |
| `AUDIT.json` | `042d1f3deb7f96799736131e857cceb6ee42810e3c454edbd85e51fb73870033` |
| `CONTROLS.json` | `3f7719c5e9f1c98e5a3623066eb1d78882f5d5b141a0ae3918c6ecfac3c000c7` |

## Scope boundary

This result supports only the declared NativeHandleBridge/X11 lifecycle composition rung. It does not establish automatic observer wiring, public CLI integration, arbitrary-backend behavior, production adoption, or the broader #2789/#3311 evaluation. The formal allocation was not rerun to publish this artifact.
