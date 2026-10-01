# Publication checksum correction

After the T1 harness completed, checksum verification found a one-character transcription error in the manually assembled `SHA256SUMS` entry for `legacy_audit_exact.py` (`...0d65d349...` instead of the actual and frozen `...0d65f349...`).

The source file itself was unchanged: its current SHA-256 is `7ab3d8895c9e8d7c80cf4ff463bac0623fb39247f8aa0d65f34941a1f8c48a40`, matching both `FREEZE.json` and the exact archived member. The frozen harness result is unchanged and was not rerun. This correction changes only the publication checksum list; every frozen source and raw result remains byte-identical.
