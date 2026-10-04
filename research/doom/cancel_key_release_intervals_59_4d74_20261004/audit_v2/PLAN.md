# Manifest audit v2 — frozen audit-only correction

Allocation: `CANCEL-KEY-RELEASE-INTERVALS-MANIFEST-AUDIT-V2-20261004-01`
Audited predecessor head: `ebe86025e7f122f0a93b841cf41211bc50b715fe`
Scope: saved evidence only; no candidate rerun, X server, game, model, GUI, or input.

## H / T / D / C / U

**H.** The predecessor's 20-row `FILES.sha256` contains three generated
Python 3.14 bytecode paths that are not in the frozen Git tree. A successor
auditor can validate all 17 actual manifest files byte-for-byte, prove exactly
those three `.pyc` entries are absent/untracked, and preserve the original
failed audit reproduction without changing predecessor bytes.

**T.** On a clean checkout at the exact predecessor head, independently run its
five-module owner/publication/composition suite once. Then run this v2 audit
once against the frozen predecessor Git tree and the published manifest. Do
not rerun the predecessor's formal candidate; preserve its `AUDIT.json` and
`FILES.sha256` unchanged.

**D.** `PASS_MANIFEST_GAP_RECONCILED` iff all 17 non-bytecode manifest hashes
match, the frozen tree contains exactly the expected 17 manifest members plus
the known unmanifested `AUDIT.json` and `FILES.sha256`, and the only absent
manifest rows are the three pinned `__pycache__/*.pyc` entries. Any other
missing, extra, unsafe, duplicate, or hash-mismatched path is FAIL.

**C.** This is a checksum-scope correction for a published fake-Xlib
construction package. It does not revise the predecessor's 16/16 candidate
tests or imply that its previous audit passed in a clean checkout. The
request-start-to-shared-XSync interval is not a physical key-up timestamp.

**U / STOP.** No live X11, application, game, model, GUI, physical input,
useful feedback, recovery, or safety result. Container diagnostics previously
stopped at the Docker content-store error (`operation not supported`); this
audit is deterministic local saved-file/Git-tree inspection and asserts no
container isolation.

## Exact protocol

1. Preserve the original candidate and original `audit.py` untouched.
2. Verify the candidate source/test pins from the predecessor freeze and the
   predecessor Git-tree inventory; hash-check the 17 published manifest files.
3. Report, but do not hash as manifest members, the explicitly unmanifested
   `AUDIT.json` and `FILES.sha256` files.
4. Retain the independent 16/16 test replay separately from this audit-only
   result. No external or live behavior is inferred.
