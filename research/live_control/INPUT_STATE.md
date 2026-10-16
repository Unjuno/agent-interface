# Historical input state around an observation — 2026-09-13

Candidate owner_v7/session_v13 attach independent-owner state samples before
capture and after capture/image preparation. A consumer can distinguish some
release-during-observation cases instead of inferring a held button from the drag
program or image alone. Existing entrypoints and frozen experiments are unchanged.

Each sample records its start/end runtime timestamps, owner revision, owned
buttons/keycodes, physical pointer mask/coordinates, actual focus, active lease
deadline, sampled time-validity and cancellation flag. `input_state` queries are
serialized by the same independent owner as input operations and do not themselves
renew the lease or increment revision.

The revision increments before each input-command attempt and before a release
attempt, including autonomous release. Failed/redundant attempts can advance it:
a changed revision is conservative evidence of intervening activity, not proof
of a successful physical state change. Revisions are local to one owner instance;
they must never be compared across a restarted owner. No cross-owner identity or
continuation protocol has been introduced in this change.

Observations expose `input_state_before`, `input_state_after`, and
`owner_revision_unchanged`. They are historical samples, not an atomic snapshot,
application acknowledgement, or current input authority when the record arrives.
Focus and external physical state can change independently of the owner's revision.
The before/after sampling window includes capture and image preparation, so it
cannot identify the exact pixel exposure time or rule out intermediate changes.

## Actual-app fault cases

`input_state_probe.py` uses private Inkscape/X11 and the real candidate backend.
It injects a bounded wait either after the real image grab returns but before the
capture wrapper returns, or in the delivery callback after both state samples.
This is controlled blocking of the worker; it does not simulate a hung X server.

| Case | State before capture | State after preparation | Result |
|---|---|---|---|
| Normal checkpoint | button 1 owned | button 1 owned, same revision | program completed; final release verified |
| Cancel during capture wrapper | button 1 owned | released, higher revision | cancelled; no held button while worker blocked |
| Expire during capture wrapper | button 1 owned | released, higher revision | expired; no held button while worker blocked |
| Cancel while delivery blocked | button 1 owned | button 1 owned, same revision | independent release happened before this historical record was delivered |

The last case is deliberately a stale-state positive control: even a matching
before/after pair does **not** mean the button is still held at delivery. Both the
sampled state and a separately sampled later release are archived with timestamps.
Future continuation must revalidate at admission against the owner and original
lease, not trust an image or unchanged revision alone.

All four cases passed in one scripted episode. Eight controlled focus-boundary
regressions passed with owner_v7, retaining same-client pointer equivalence,
foreign-client rejection and exact keyboard/mixed-input focus semantics.
`audit_input_state.py` verifies launch source hashes, ten exact AIT/PNG frames,
sample/capture/delivery ordering, state transitions, terminal release records and
the episode's owned-process cleanup. This is correctness evidence for these
cases, not a reliability or latency distribution.

## Remaining work

There is still no replacement of an in-flight path, owner-instance identity for
continuation, or atomic claim about pixel/input state. Extra queries and metadata
have not been benchmarked for overhead or model token cost. This is candidate core
state semantics/churn, not runtime promotion, freeze qualification or human-speed
parity. Next define a bounded continuation admission contract using original
deadline/target, current owner state and observed sequence; test obsolete replies,
release races and foreign-window changes before actual assistant use.

```sh
python3 research/live_control/audit_input_state.py
python3 research/live_control/input_state_probe.py \
  --out research/live_control/results-local/new-input-state
```
