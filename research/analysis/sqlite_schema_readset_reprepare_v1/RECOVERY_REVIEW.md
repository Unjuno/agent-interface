# #4114 recovery review (2026-09-28)

This is an additive recovery of the original 2026-09-22 branch evidence. All 18 predecessor files are preserved byte-for-byte; this review does not amend the original report or formal result.

## Disposition

- The predecessor reports one frozen invocation, 48/48 subprocess cases, zero reruns/replacements/tuning, a passing independent SQLite/raw audit, and 8/8 rejected corruption controls. These are reported historical results, not a new formal execution.
- Recovery reconstructed the seven Base64 parts to the declared XZ archive SHA-256 `efe2a55f2b0f85bcf2921243c622c6e74f20b56a6e99fc67e3e8d9a2eb4dd0da` (22,568 bytes), safely inspected/extracted its 256 members, and reran `audit.py` read-only against the recovered raw. The audit exited 0 and its parsed output matched the committed `AUDIT.json`; its canonical audit output SHA-256 is `752a5c6e018f463e58fe39c0934d0d5187254145a60fb327a24fe94f701a7b7e`, as recorded in `RESULT.json`.
- The copied-evidence corruption checker rejected all 8/8 mutations again. This is audit/control replay only; no SQLite formal cases were rerun.
- Archive-internal file-manifest reconciliation is **254/255**, not 255/255. `MANIFEST.json` expects `MANIFEST_STDOUT.txt` to be 0 bytes with SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; the archived member is 20 bytes with SHA-256 `4ebf4c2d...` (the full digest and bytes remain in the preserved archive). This discrepancy is packaging/provenance incompleteness. The archive-level digest matches, and the scientific audit passes, but packaging integrity remains HOLD pending source-side explanation; no evidence has been rewritten to make the manifest pass.
- The recovery audit ran on the available macOS host (Python 3.14), not the originally declared Linux x86_64 / CPython 3.13.5 container. OrbStack was not used because peer-owned container activity was present. Thus this is an independent host replay, not environment reproduction.

## H/T/D/C/U boundary

**H:** Schema-version-scoped dependency replacement may avoid stale dependencies and lifetime-union false invalidations in the frozen cooperative singleton-view family. Existing formal result supports only that bounded claim.

**T:** Historical formal design: 3 policies × 8 scenarios × 2 fresh subprocess repetitions = 48. Recovery work was read-only archive reconstruction, independent audit, and corruption-control replay.

**D:** Historical formal decision remains `PASS_SCHEMA_SCOPED_SQL_DEPENDENCY_REPLACE_SCOPED`; recovery integrity disposition is `HOLD_MANIFEST_ONE_FILE_MISMATCH`. Do not represent these as one unqualified PASS.

**C:** The archive SHA and audit are independently reconciled. The one internal manifest row mismatch and host/container environment difference remain explicit limits.

**U:** No broader SQL completeness, performance, production, GUI/model, crash-durability, or security claims. Do not promote to runtime based on this recovery.

## Next action

Retain the predecessor branch until this evidence is merged and independently read back from main. Investigate the 20-byte manifest stdout against original capture provenance before claiming complete packaging integrity. No new formal allocation is authorized by this recovery.
