# R24 input-free preparation history

No fixture was started and no native input was sent during these preparation
checks. The initial predecessor check stopped because the recorded R23 manifest
hash did not match the raw bytes in `origin/main`. After recording the actual
raw hash and its semantic fields, one check stopped because the frozen
conditions omitted the manifest path. The final input-free preflight passed
with `PASS_WITH_RECORDED_PREDECESSOR_HASH_LIMITATION`; all source, packet,
platform, and independently parsed R23 semantic checks passed. The mismatch is
retained as an explicit limitation; the R23 packet is unchanged.

The current-main and `codex/win32-post-recovery-action-r23` raw blobs were
independently read with `git show`: each is 91,538 bytes and hashes to
`e4106c26a078dd57a1379e456506f983b1fa5761ed7f00168b145b961807ea5f`.
R23 `SHA256SUMS.final` and `audit_followup.json` both claim
`b46e11d7abc460cf1160960fbf683462f0a5c9bb13bffac33f0844e8f3becda8`.
