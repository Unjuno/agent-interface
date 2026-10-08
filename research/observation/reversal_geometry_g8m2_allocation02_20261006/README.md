# #4387 supplementary allocation g8m2-02

This directory preserves the separate 2026-10-06 allocation from closed-unmerged PR #8241. Main already contains allocation g8m2-01 at `reversal_geometry_g8m2_v1/`; this package is stored under a distinct path so its reports, freeze, and raw capsule do not overwrite allocation 01.

The retained report records a fresh 360-row synthetic matrix, 26 wrong singleton directions from the unchanged legacy heuristic, zero wrong singleton directions from the feasible-set candidate, and 126 informative candidate singletons. It also records an independent separately structured exact-rational audit and the limits of the bounded known-speed, at-most-one-reversal model. This is corroborative evidence for the same scoped question, not a new deployment or product claim and not a replacement for allocation 01.

The originally proposed matrix was accidentally run during construction. Its bytes and `STOP_WORKFLOW_INTEGRITY_PREEXPOSURE` disposition remain in the capsule and are not pooled with the fresh allocation. The package preserves the original source branch files byte-for-byte; `SHA256SUMS` records the compressed capsule digest. The combined capsule digest was checked against that record, and its 22 tar members were inspected as flat regular files without executing `unpack.py`, the candidate, the auditor, or tests.

No experiment, candidate, auditor, or helper was rerun to prepare this rescue. Keep the allocations separate, preserve the pre-freeze STOP, and require independent review before any integration.
