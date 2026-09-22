# Publication validation

Post-formal, pre-PR readback.

## Lossless evidence capsule

Decoded XZ/TAR: 23,944 bytes, SHA-256 `899ce14def44b21f63eab9007bab8a301c824278e1460a861dbc36a9a10e9987`.

Restored corpus: 39 regular files / 434,651 bytes. `PACKAGE_02.json` binds every member path and SHA-256. The bounded unpacker rejects existing destinations, missing parts, altered part bytes and reordered manifests.

Local `test_repo_unpack.py`: 5/5 methods pass.

Final GitHub part blob identities exactly match the locally computed Git blobs:

| part | Git blob |
|---|---|
| part00 | `f0c0327964a385d4aabeb9225f430a0a23dc44ae` |
| part01 | `cd3fe8eb149e309f147c1aebd23edf024bf7e5b2` |
| part02 | `e5513f40bc718dc5f04e7d4848d9d8f97d44fe09` |
| part03 | `058ad142570c1199a95b226bcd618faf3c527789` |
| part04 | `4fb55912d01a7bd91a5ff1d6cf4a0bb1031ffd54` |
| part05 | `4d7c50c8ea4e07c76a0e68d2022e80b7d5a22424` |

Manifest/package/unpacker/test blobs also match local originals:
- ARCHIVE_PARTS_02.json `9304d892895c24433875d6492a74bf5d48feecca`
- PACKAGE_02.json `f10445d9eb27ce24971c86756bea8fc67d0d26eb`
- unpack_repo.py `1430fd9ec1e5c06735777d2af6a4840092bf5a19`
- test_repo_unpack.py `c73091ca879dfc121a49ac3eeeff128dbf7d695c`

The initial Base64 publication transcription defects were detected by this identity check and corrected before PR creation; they are not hidden.

## Scientific-integrity check

A separate readback found the preformal `PREMEASUREMENT.md` self-hash mismatch documented in `STATUS_NOTE.md`. That mismatch changes the final allocation02 disposition to HOLD even though the raw audit and numeric gates pass. The public preformal file is intentionally not rewritten after formal execution.
