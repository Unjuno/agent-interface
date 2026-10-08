# #7949 A05 — independent-auditor-corrected external-transition successor

## H / T / D / C / U

**H.** An event-complete external write after an action invalidates a revision-bound recovery certificate. A fresh certificate can be evaluated from the new state while preserving the external field; an event-sequence gap must be accepted by the auditor as the expected fail-closed `UNKNOWN`, not misreported as an audit implementation failure.

**T.** Three cases on authored three-bit states, horizon 1: baseline `100→000`; external event `100→101` at revision 1→2, stale rev-1 certificate yields UNKNOWN and refreshed rev-2 certificate recovers to `001`; sequence-gap record is `UNKNOWN_EVENT_CHAIN`. Candidate replay and sequence search are checked by raw-only audit that independently validates malformed-history UNKNOWN cases and exhaustively enumerates valid recovery words. Before freeze, unit tests directly exercise both a valid gapped-case raw fixture and a forged acceptance mutation against the auditor core.

**D.** PASS only if baseline is uniformly recoverable; stale certificate is UNKNOWN; refreshed state reaches `001` preserving both external bits; gap is UNKNOWN with no recovery; audit errors=0 and three frozen output mutations are rejected. Any unsafe accept or external-field loss is FAIL; audit error is HOLD; execution deviation is STOP. One candidate/one auditor, no retries.

**C.** This tests only the Issue's finite intervening-write minimum case. A complete authored event log does not establish real application event coverage or certificate authenticity.

**U.** No GUI/application/runtime/user-effect/safety claims. A01's primary finite outcome-set result remains its own bounded PASS; A02–A04 remain unchanged historical STOP/HOLD records.

Runtime and provenance: native macOS standard library; no container-isolation claim (OrbStack read-only image inventory had returned `operation not supported`). Base `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`, isolated research branch, additive A05 path. Freeze hashes and counts will be posted to Issue #7949 before formal execution. Candidate stdout and exit are captured in a single command call; auditor runs once only after reported candidate exit 0.
