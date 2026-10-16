# Nullable key identity audit result (#5486)

**PASS_KEY_IDENTITY_AUDIT_HOST_ONLY**. The original PR #5467 auditor's fail-open behavior was reproduced; the additive candidate rejects explicit-key and cleanup-key corruption.

## H/T/D/C/U

- **H:** Including nullable `key` in release identity accepts pristine input and rejects tampering for explicit releases and autonomous cleanup.
- **T:** One frozen CPython 3.11.9 host run against the unchanged three-row #5467 inventory/raw, then a separate raw-only audit. Candidate SHA-256 `79f95eadb29bc6cc35036c6ff424cb284e55849ecd76ccd2a841ae186a18d1cf`; runner `044465ed408dde88d680e24d05ff507ec8564756a297da4edecbcd767017b20c`; independent audit v2 `79758680c8dd37cd604903c84a317ebdfb22f07ec9471bfe962428efbdc2ba3d`.
- **D:** Pristine candidate errors=[]; explicit key mutation rejected as `release_identity_mismatch:explicit-a-01`; cleanup null mutation rejected as `release_identity_mismatch:cleanup-b-01`; missing key and missing row rejected. Legacy source accepted both key mutations. Independent audit exit=0, errors=[].
- **C:** Host-only in-memory; no local files, Docker/X11/MAP01/model/GPU/network. #5085 has no transferred shared-container lease; C: free space is zero.
- **U:** Synthetic audit integrity only. No live owner emission, X11 key-up bracket, physical occupancy, useful feedback, bounded recovery, or real-time-control outcome is established.

Executed runner stdout SHA-256 `a3a960e3007d008b6af01578780563e8aead5397f709280b514d99e7db74dbe5`; independent audit stdout SHA-256 `f36fcaf99919e13589287c005c3d9a67d230256665919974acc5ac65d25964c8`. See RUN.json, AUDIT.json, and the pre-run freeze amendment.
