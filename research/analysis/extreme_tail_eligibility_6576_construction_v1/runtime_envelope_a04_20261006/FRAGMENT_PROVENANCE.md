# Archived evidence fragment — invalid and incomplete

The original research branch briefly contained `EVIDENCE.b64.part-00`, added in commit `f3067b23b1f2a2eaef8e21824423ae42b2bdf4e` and removed in `e52f0747742f3f9a9156a8f8aa46c7322dc78d6f` as an unverifiable archive transcription. The exact fragment is preserved here under an explicitly unverified filename so the attempted transfer is inspectable without suggesting it is usable raw evidence.

- Original Git blob: `8a39bc891ccf6edde185d723f2f1a91f578556c6`.
- Actual fragment: 20,023 bytes; SHA-256 `d978b630a59f027e90ce67fd6910e8e97529732520dc8be38ae922d09fdd17f5`.
- `EVIDENCE_RESTORE.md` declared the expected part-00 SHA-256 as `18994e92fc60c50da07c711f4427726866855ad260848a81836e79c9c1fd4d4f` and required nine parts (`00`–`08`) to reconstruct a 360,664-byte archive.
- No parts `01`–`08` occur in the available A04 branch history. The preserved part-00 fails its declared digest; base64 decoding exits 1 after only 6,970 bytes.

This fragment cannot reconstruct `EVIDENCE.tar.xz` or the missing formal raw. It was not decoded into a replacement result, combined with invented data, or used to rerun the old allocation. `RAW_PROVENANCE.md` remains authoritative: `remote_raw_complete=false`.
