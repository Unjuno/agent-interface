# Recovery status: source recovered; formal evidence delivery HOLD

This additive snapshot preserves the exact 17 files present at remote branch
`research/subscriber-wait-order-4308-20260924-sw21`, head
`d2852e1397f852838e7d8586c76bacffd4158fe5`. It does not rerun or rewrite the
reported 24-case allocation.

## Exact source recovery

The branch's `SOURCE_MANIFEST.json`, three source-capsule fragments and bounded
data-only `unpack.py` restore nine files into a fresh directory. Restoration
verified archive SHA-256
`a19a63cfd78035ec8a507e6883b54606b3ab88e320654f5c266cf2544b39a385`; all six
restored Python files passed an in-memory syntax compile. The test suite has
seven tests but depends on `construction/c01`, `construction/c15`, and
`construction/c22` fixtures, which are not included in this branch's source
capsule. Running it against the restored source therefore produced one
failure and three errors from missing fixture paths/metrics; this is not a
formal result or a candidate-code PASS.

## Formal-evidence limitation

All 12 committed `EVIDENCE.part00.b64`–`part11.b64` fragments were preserved.
Strict base64 decoding yields 54,000 compressed bytes (SHA-256
`8a67a1aa3cdb741fdc29239b181bec0e29606a774cf834a2456d45a5b5bce9af`), but the
XZ stream does not reach EOF and its decoded JSON is truncated at byte
1,483,572. The branch has no evidence manifest/restorer, complete archive,
formal raw-only audit, or control outputs. Thus the Issue-reported
`PASS_SUBSCRIBER_ACK_WAIT_ISOLATION_SCOPED` remains historical, not
independently reproducible from this package. Do not interpret the partial
decoded prefix as rows or recompute a result from it.

## Verification and disposition

- All 17 original branch files are preserved byte-for-byte by Git blob
  identity; the recovery note is the only new file.
- Source archive restoration succeeds; the formal evidence archive check
  fails closed on the missing XZ terminal marker and truncated JSON.
- No formal event, worker, or control was rerun, and no missing bytes were
  reconstructed.

Disposition: `HOLD_FORMAL_EVIDENCE_ARCHIVE_TRUNCATED`. Preserve the Issue's
reported result and the exact available source/raw fragments separately. A
stronger evidence claim requires authoritative recovery of the complete
original archive, a hash-bound manifest/restorer, and successful
repository-only raw audit and corruption controls.
