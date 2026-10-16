# Same-hold continuation admission — 2026-09-13

Follow-up: [guided pointer reply pilot](GUIDED_POINTER.md) integrates the worker
yield and reply protocol in newer candidates. The component evidence below remains
the frozen owner_v8 result.

Candidate `input_owner_v8.py` adds an owner-instance ID and `continue_move` to the
existing independent input owner. This addresses the admission boundary needed
by Issue #2's bounded continuation direction. It does not yet replace the running
executor's path or implement a planner-facing continuation protocol.

The owner creates a random identity per instance and includes it in `input_state`.
A continuation supplies that identity, an expected owner revision and an absolute
point. Admission and movement run on the same serialized owner thread:

1. Require exact payload fields, current owner identity and current revision.
2. Require the original active lease object, exactly one owned button, no held keys,
   and that button still physically down according to X11.
3. Apply existing pointer focus/client, geometry, hit-surface, lease/cancel and
   coordinate checks before moving.
4. Advance revision and mark the returned admission record as a continuation.

The lease deadline and original target bindings never change. A continuation
does not press a button or revive a released hold. Two queued replies with the
same revision cannot both succeed: the first successful command advances revision
before the second is checked. Revisions are scoped to the random owner identity,
so the same integer from a restarted owner is not sufficient.

Candidate owner-call payload (revision/identity must come from this live owner):

```json
{"owner_id":"owner-instance-id","expected_revision":17,"x":130,"y":120}
```

These are research backend coordinates, not a new portable public coordinate
contract. They intentionally remain behind the owner boundary while coordinate
frame abstraction is unresolved.

## Executed evidence

Two controlled private-X11 cohorts completed 11 and 12 checks. The second adds
an external physical button release, distinct from release requested through the
owner. The fixture explicitly sets its test windows and active-client property;
this is component validation, not a window-manager or application task benchmark.

- A valid continuation moves while retaining the same hold and lease deadline.
- Duplicate replies and replies after intervening input are rejected without motion.
- Replies after owner release, external physical release, expiry or cancellation
  cannot revive input.
- A different focused surface, changed geometry or mixed keyboard hold is rejected.
- Two concurrent callers using one revision produce exactly one admission.
- A retired owner's identity is rejected even when paired with the new owner's
  current revision and lease.

Source manifests, assertions/results and release records are retained under
`results/continuation-admission-01` and `02`; all owned processes exited. The
component's queued calls retain existing bounded caller watchdogs. This is not an
end-to-end atomic screenshot/input guarantee or an assistant latency measurement.

## Integration gates still open

Owner revision is not observation freshness: the application can change without
any owned input. A broker still needs observation sequence/age and explicit target
dependencies. The current executor is not paused/replaced by this operation; do
not call it alongside a preplanned tail that would later overwrite the correction.

Next integrate an explicit yield point, one pending response, original deadline,
bounded update count/duration and verified final release with the existing
observation stream. Stale sequence, response races, delayed delivery and owner
restart need combined broker/owner tests before actual assistant manipulation.
The current component is time-bounded by its original lease but does not itself
cap the number of continuation requests within that lease.

Issue #3's selectable visual grid remains a separate presentation experiment. It
must preserve source-frame identity and use fresh matched cases; it should not
hide application drag-response errors or silently add planner round trips. The
Issue #2/#3 update timestamps were checked this turn and had not changed.

This is candidate core-semantic churn, not runtime promotion, freeze qualification,
path-replacement completion, token savings or human-speed parity.

```sh
python3 research/live_control/continuation_admission_probe_v2.py \
  --out research/live_control/results-local/new-continuation-admission
```
