# PR6948 successor rescue

Source c32d4d6f683586e87047ae24f3b6664cb6d95d09 retains26 original packet
files unchanged. Current primary CLI command receives the two maintained
lineage modules (8 tests); newer dedicated MotorState discovery is preserved.
Fresh Python3.12 optimized execution:8 tests PASS. Full current workflow
command remains to be verified before delivery.

Original PRIOR_WORKFLOW.yml.txt is empty despite the prior workflow blob
aae4a608f14b161cf2de814cdaa7e5819b07c562 containing682bytes. The successor
PRIOR_WORKFLOW.actual.yml.txt preserves that real blob separately, without
rewriting the historical inaccurate capsule. The original REPORT says the
obsolete workflow was retired. That deletion is not yet adopted here: retain
the actual old job until its regression behavior and replacement coverage are
checked. No checks are cancelled or removed to make PR7187 pass.
Original historical FAIL logs and Windows CRLF remain unchanged.
