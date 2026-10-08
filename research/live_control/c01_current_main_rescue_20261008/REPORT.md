# Issue #6501 C01 current-main evidence rescue

Date: 2026-10-08 JST
Base: `fabdb1de8273e8a87dfb2bea53856079da997998`

## H/T/D/C/U

- **H:** The unique C01 Windows pending-I/O observation packet is useful as a narrowly scoped prerequisite record, but is not present in current main and must not be confused with later cancellation allocations.
- **T:** Preserve the already-consumed C01 packet byte-for-byte on current main; verify its committed manifest and repository indexes without rerunning the Windows probe or either historical auditor.
- **D:** The 33-file C01 packet subtree was restored from closed rescue PR #8232's head `29bee582ebb4b367e4dc28e14102a2bb5d047d97`; its complete `SHA256SUMS` covers 32 packet members. Only C01 evidence and navigation/report files are carried. The old PR merge history and unrelated current-main deletions are excluded. No runtime code, workflow, candidate, or auditor source is activated.
- **C:** The original C01 report records one Windows 11 / CPython 3.12.14 allocation, 27 ordered events, three positive pending-read versus `Event.wait` control pairs before any write, one ordinary byte transfer, joined threads, and verified handle/CRT-FD closure. Saved audit V2 independently reconstructs the events and rejects ten corruption controls. The original audit path-lookup failure remains preserved. Local current-main manifest/index/diff results are recorded in `COMMANDS.txt` after execution.
- **U:** `PASS_OWNED_THREAD_PENDING_METHOD_ONLY` is an observation prerequisite only. It proves no cancellation efficacy, instantaneous kernel-entry identity, safe thread-pool reuse, task effect, authority, recovery, portability, or performance. C01 is consumed; no probe/auditor rerun, native allocation, or source adoption is implied. #8232 was closed unmerged; this additive successor does not inherit its votes or Issue #6501 application authority. Fresh review, current-tree applicability, Issue ownership/application gates, required CI, and sole-owner main application remain separate.

The original packet is retained unchanged at `research/concurrency/windows_pending_method_6501_01a0ff58_c01/`. Its first failure and corrected saved-data audit are both preserved. Later #6501 T02/T03/P02 are distinct allocations and are not part of this rescue.
