# PR6948 successor rescue

Source c32d4d6f683586e87047ae24f3b6664cb6d95d09 retains26 original packet
files unchanged. Current primary CLI command receives the two maintained
lineage modules (8 tests); newer dedicated MotorState discovery is preserved.
Fresh Python3.12 optimized execution:8 tests PASS. Full current workflow
command remains to be verified before delivery.

First rescue inspection mistakenly inferred an empty original from the diff
line-count display. The first successor verifier failed (expected0bytes,
actual682). Exact Git/file comparison proves PRIOR_WORKFLOW.yml.txt already
contains the complete682byte original. The separately added copy is identical,
not a correction to historical evidence. This mistake is retained explicitly.
The obsolete automatic job is now retired after executing its unchanged fixture:
3methods,2failures at EVIDENCE_DIGEST_MISMATCH because the altered receipts
leave their sidecar evidence digest stale. The historical fixture and failure
records remain unchanged. Maintained freshness3 and identity5 tests now run
through the existing three-OS CLI entry, with MotorState discovery retained.
No checks are cancelled or removed to make PR7187 pass.
Original historical FAIL logs and Windows CRLF remain unchanged.
