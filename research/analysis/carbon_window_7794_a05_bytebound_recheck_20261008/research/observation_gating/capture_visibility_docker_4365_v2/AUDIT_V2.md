# Versioned read-only auditor correction

The frozen `audit.py` was run once on the complete formal output and returned `FAIL_RAW_AUDIT` for four `window_pixel_mismatch` findings in CHILD_HALF/FULL. Preserve that source and report as-is.

A separate local Docker pixel diagnostic decoded the already-captured client-window and root-screen raw bytes: CHILD_HALF contains exactly 4,800 parent-color and 4,800 child-color pixels in both frames; CHILD_FULL contains 9,600 child-color pixels in both frames. Thus the window-client drawable capture includes direct-child pixels in this environment. The frozen auditor incorrectly expected the entire window-client capture to remain parent-colored for these two child conditions, despite the separate root geometry oracle already passing.

`audit_v2.py` changes only this read-only pixel oracle: it expects the preregistered child rectangle's fixed color in CHILD_HALF/FULL and the parent color elsewhere, while preserving all other source, raw digest, geometry, assessor, cleanup, count and provenance checks. It reads the original frozen source manifest and the same immutable `formal01` bytes. It does not rerun the producer, alter source/result/case/raw evidence, or relax the 12/24 and 4/8 gates. Both auditor results are retained side-by-side; v2 is supplementary evidence and does not erase v1's false rejection.
