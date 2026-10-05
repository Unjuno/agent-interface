# Deny-unknown partial record schema

Forward correction of helper atd4c638b9f, not a historical result rewrite.
Peirce review of d4c638b9f found Critical0/Important0 within bounded helper;
Minor missing direct malformed-type/argv/nonpositive-clock controls retained.
Main then checked actual frozen producer fields and found the original deny
list did not cover initial/submit/after_notification/wait_start_ns or unknown
future fields. Five real negative subcases failed before this correction.

V2 uses only a fixed allowlist of early failure metadata; every extra field
is refused. Eight package methods pass normal/optimized host and own offline
container. Raw RED5/GREEN/container receipts and separate saved compatibility
record retained. Fixed saved E03 still returns STOP/scientific_passfalse/
exposureNOT_ESTABLISHED. No producer/game/official-auditor rerun.
Frozen startup entry/test/protocol remain unchanged; classifier/test are new
construction, not inputs to the already consumed startup run.

MANIFEST-v2 remains a record of d4c638b9f payload; classifier/test have changed
since that version, so do not verify it against this later tree and treat the
expected historical mismatch as corruption. MANIFEST-v3 is current payload
coverage; original startup MANIFEST and PREPARATION_PINS still match.
Full outer audit integration and actual receiver-fault E04 remain pending.
