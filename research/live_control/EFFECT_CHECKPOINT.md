# Non-final artifact checkpoint candidate

Runtime v29 adds effect_checkpoint queries without reserving a final program or
closing input admission. Socket v14/cursor v6/request boundary v3/command registry
v3 route them by their query request identity. The existing default stack stays
unchanged. Queries sample an existing application output artifact, not arbitrary
caller-supplied filesystem paths or hidden application engine state.

Example for the private browser fixture (after is the latest received cursor):

```json
{
  "after": 24,
  "events": ["effect_checkpoint"],
  "timeout": 5,
  "request_id": "check-before-confirm",
  "read_request_id": "check-before-confirm",
  "command": {
    "op": "effect_checkpoint",
    "contract": {"kind": "saved_form_value", "expected": "t991029"}
  }
}
```

This is a socket query, not a prepared_exchange_v6 boundary mode. A new snapshot
requires a new query ID. Reusing an identical ID retains the existing at-most-one
forwarding semantics; it does not refresh evidence. Cursor prefixes still retain
other requests' records. Missing query identity is not accepted as a match.

The query returns task_success=null regardless of the sampled predicate. Its
evidence status is VERIFIED only when the sampled saved fields match the declared
contract. A missing, unreadable, malformed, oversized form artifact or mismatch
in the still-open observation window remains UNKNOWN. There is no closed-window
CONTRADICTED result in this API. The first worksheet's specified cells can also
be sampled through the existing saved_effect helper; that branch has not yet had
a v29 Calc integration run. This is not the full Issue #34 effect contract.

The form sampler reads at most 65537 bytes and rejects values beyond 64 KiB,
parses the same bytes whose hash it reports, and compares the complete field
mapping with exactly value=[expected]. The reused workbook sampler has no new
file-size or execution-time bound. Neither proves atomic filesystem capture,
durability, actor attribution, forbidden-effect absence or preserved properties.
Every result explicitly leaves attribution unestablished and grants no authority.
No observation refresh or input lease extension occurs.

## Worker and lifecycle

One daemon worker may sample at a time, with no query queue. A concurrent request
returns top-level status=UNKNOWN, reason=verifier_busy, task_success=null. Completed
samples are nested under evidence; callers must distinguish these response shapes.
Caller contract/metadata are copied before the worker starts. Exceptions remain
unknown. The command reader does not run the verifier synchronously, but this is
not a hard cancellation or response-latency guarantee: GIL/CPU contention, storage,
the existing shared emitter/stdout and locks can still delay work. Closing the
service suppresses later publication; it does not interrupt a stuck verifier.
Results may already be historical by delivery time.

## Evidence

The first integration attempt failed before query forwarding: socket v13 still
used command registry v2, whose operation allowlist rejected effect_checkpoint.
The error and frozen candidate source hashes are retained in
results/checkpoint-confirmation-01. Socket v14 uses registry v3 with the explicit
new operation. No rejected request was silently replayed in that session.

The corrected scripted confirmation fixture run, checkpoint-confirmation-02,
uses terminal mode for the first submission, samples UNKNOWN while unsaved,
admits another program to check confirmation and save, then samples VERIFIED.
Both query responses have task_success=null and correct query identity. No
independent evaluation is emitted until explicit finish. That final legacy finish
scores true without an action-attribution claim. The test verifies 22 exact
frames, three admitted/released programs, ordered full delivered prefixes,
source hashes, and retained HTTP attempts [false,true] after cleanup.

Individual controls cover missing, mismatching, malformed and oversized form
files, a matching sample, busy behavior, caller-mutation isolation, closed-service
rejection and verifier exceptions. Identity controls cover same-ID deduplication,
payload conflict, unsupported commands, other-request prefix preservation and
missing identity. See results/effect-checkpoint-01 and checkpoint-identity-01.

The probe retains inherited unreachable premature-final branches from the earlier
two-condition harness; results explicitly identify the one executed checkpoint
case. This is scripted known-fixture evidence, not actual assistant use or an
unfamiliar application completion policy. No model token, latency improvement,
human-tempo or cross-domain claim. Next exercise this candidate in actual self-use
and Calc, and test slow-verifier/cancellation contention before promotion.
