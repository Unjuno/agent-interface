# Custody reconciliation addendum

This addendum repairs the published-byte representation of the immutable #7159 archive without changing its original manifest or replaying its assay/auditor.

## Finding

The original source tree is `0e58fb7882c5a726647cad8e77a1b3536d4eb7ea`. Its `MANIFEST.json` binds 12 members. Two saved source snapshots (`assay.py.txt`, `audit.py.txt`) match their declared bytes directly. The remaining four text records and six base64 SQLite images were stored with LF line endings, while the manifest binds CRLF bytes. Replacing each LF with CRLF reconstructs the declared byte count and SHA-256 for all ten members. No other byte or payload transformation is applied.

## Repair and verification

- The original 13-file source subtree and `MANIFEST.json` are unchanged on the predecessor branch.
- This successor restores CRLF only for those ten manifest-bound members. The two source snapshots remain byte-identical to the predecessor.
- The adjacent `.gitattributes` disables text normalization in this custody directory so the Git blobs retain the manifest-bound bytes.
- Validation reads the staged Git blobs, not checkout bytes: all 12 manifest members must match both declared byte count and SHA-256. The manifest itself remains unchanged and is not self-authenticating.
- No embedded SQLite image was decoded or opened; no historical candidate, assay, auditor, or native experiment was rerun.

The staged-blob readback matched these unchanged manifest entries:

| Member | Bytes | SHA-256 |
| --- | ---: | --- |
| `assay.py.txt` | 2564 | `e565ff88d553c0e6ea49dc737469caf34488016825b98d78087de88491202553` |
| `AUDIT.json` | 290 | `10161d76fea71c7d82dc2289ebacf447b45ddbe923fed2c82180842884f29966` |
| `audit.py.txt` | 955 | `6d92a731a933b52130ceca6c5b2d7467abc3e01719427a6d0ffa4f536adf8e79` |
| `FREEZE.json` | 1049 | `14d7aecad26d1ce22388911b75ed643533418022fb0862818fe173d92bcdeb0c` |
| `generation_join-0.db.b64` | 10926 | `9056b6c62393fd83ccb8b7ffcfc9138f5a9db6772eab72b00470baa6a4da05df` |
| `generation_join-1.db.b64` | 10926 | `fe11d28fd45ba9d8b94655b11dd26fe86cfd8c7bac421de4e931dc69ada1675b` |
| `RAW.json` | 2257 | `079f4762b6456cf4d19b25c14ac9fd565883a1a003036bafd25352d02925ca13` |
| `REPORT.md` | 1897 | `2ef5fc0dce21f00f3f67598d31f1d63f1ce5b2fe76c8dfff8ffd56742632296c` |
| `snapshot-0.db.b64` | 10926 | `9056b6c62393fd83ccb8b7ffcfc9138f5a9db6772eab72b00470baa6a4da05df` |
| `snapshot-1.db.b64` | 10926 | `fe11d28fd45ba9d8b94655b11dd26fe86cfd8c7bac421de4e931dc69ada1675b` |
| `split-0.db.b64` | 10926 | `9056b6c62393fd83ccb8b7ffcfc9138f5a9db6772eab72b00470baa6a4da05df` |
| `split-1.db.b64` | 10926 | `fe11d28fd45ba9d8b94655b11dd26fe86cfd8c7bac421de4e931dc69ada1675b` |

## Qualification

This closes only the published-byte custody discrepancy. It does not establish freshness, request origin, safe retry, a real task effect, or a general consistency guarantee. The original PR remains the immutable record of the initial mismatch. Fresh nonauthor content approvals and current-tree/application authorization are still separate gates before integration; earlier votes and application certificates are not transferred.
