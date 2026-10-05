# Post-formal baseline comparison — Issue #8040 A01

This is a read-only calculation over the already frozen A01 public trace, saved candidate output, truth sidecar, and passing raw-only audit. It does not invoke the candidate CLI or auditor CLI, change the A01 disposition, alter frozen files, or constitute a second formal allocation.

It reports three declared policies: restart the generic procedure at operation 0; unconditionally stop/yield; and use the saved effect-indexed map. For current-generation rows with correctly bound receipts, restarting at zero would repeat 8 known VERIFIED prefix effects across the fixture. Unconditional stop would continue in 0 rows. The effect-indexed candidate advances to a correct later generic cursor in two eligible verified-prefix rows (one and two operations verified), while every emitted row still has `execution_authorized=false`; it yields on UNKNOWN/partial/malformed/stale cases and represents end-of-macro as `CURSOR_AT_END_UNVERIFIED`.

The comparison is deterministic bookkeeping over the fixed records. It does not simulate real replays, measure effects or count the theoretical repetitions as observed. The result remains scoped to the authored finite model and the trusted typed-receipt input contract.
