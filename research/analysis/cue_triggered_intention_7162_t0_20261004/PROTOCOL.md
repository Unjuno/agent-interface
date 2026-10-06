# Frozen protocol — H / T / D / C / U

**H:** Typed lifecycle memory and a validated packet recall an intention on an
exact object/state re-encounter only while it remains PENDING; they do not
revive COMPLETE, CANCELLED, SUPERSEDED, UNKNOWN_EFFECT, or AUTHORITY_REVOKED
records. Recall only requests inspection/revalidation and never grants input.

**T:** Enumerate six lifecycle states × three object/state cue types × three
policies (PLAIN_TEXT, TYPED_LIFECYCLE, RESUMPTION_PACKET), 54 policy outcomes.
Independently reconstruct the table and inject four corruptions: ignore
terminal lifecycle, ignore object identity, turn recall into input authority,
and treat UNKNOWN_EFFECT as PENDING.

**D:** PASS_METHOD_SCOPED requires exact agreement with the independent oracle,
zero typed/packet recall for any non-PENDING lifecycle or non-exact cue, at
least one retrieval of the eligible PENDING/exact-cue control, no input
authority in any row, and rejection of all four controls.

**C:** The ordinary #5404 resumption packet may already provide equivalent
cue/identity/lifecycle checks; adding a distinct object-memory mechanism may
not improve over that packet.

**U:** Synthetic table only. An exact cue does not prove the world still
matches prior assumptions. No model, human, GUI, latency, action, or live
security claim follows. The policy deliberately requires revalidation.

Runtime is host standard-library Python. Formal candidate and auditor each run
once after preregistration; no retries.
