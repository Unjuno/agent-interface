# Publication helper history

Formal science was already complete before these steps. No formal row was rerun or changed.

1. `unpack_failed_v0.py` attempted to decode each Base64 text part with `validate=True` while retaining the file's terminal LF. The first read-only restore attempt exited nonzero with `binascii.Error: Only base64 data is allowed`. `RESTORE_ATTEMPT_01.*` preserves that failure.
2. `unpack.py` changes only the publication helper: it removes ASCII whitespace from each text chunk before strict Base64 decoding. Archive bytes, archive digest, formal raw evidence, frozen source, decision gates and audit source are unchanged.
3. A fresh restore is required to reproduce every retained member hash and the original `AUDIT.json` byte-for-byte. This is publication verification, not another experiment allocation.

4. The second read-only restore attempt reached the XZ decoder but the initial 64 MiB decompressor memory cap was below the archive preset requirement; `unpack_failed_v1.py` and `RESTORE_ATTEMPT_02.*` retain that publication-only failure.
5. `unpack.py` raises only that bounded decompressor cap to 256 MiB. Archive bytes and all formal evidence remain unchanged.
