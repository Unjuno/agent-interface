# Read-only progress to an already-issued clock

Follow-up: [actual live reader use](PENDING_CLOCK_LIVE.md) combines retained history
and an original image before explicit successful move/save. One read was needed;
this is a single integration result, not paired performance qualification.

`read_pending_clock_v1.py` addresses the historical clock boundary observed during
[actual Inkscape recovery](POINTER_VIEW_RECOVERY.md). It accepts only a report with
one existing clock attempt and `program_sent: false`. It never issues a clock or
input command. Further requests contain only a received cursor, clock event filter
and bounded wait. Each request/reply is persisted and combined with the checked
received-history assembler.

The reader looks for the original request's command echo and following clock.
Duplicate echoes, a command interleaved before that clock, invalid clock fields,
unresolved transport statuses, history inconsistencies, or exhausted read bounds
leave `needs_reconciliation`. A found clock yields
`own_clock_received_review_required`, not permission to submit input. It does not
refresh images, assert current content, check task effects or retry a program.
The caller must still review intervening observations and the sequence relationship.
Already-submitted attempts are outside this helper's scope and rejected before I/O.

Default bounds are at most four read exchanges and a two-second cooperative I/O
budget (maximum configurable five seconds). Each network exchange uses the
remaining absolute deadline. Parsing, file persistence, history assembly and OS
scheduling are not hard real-time bounded; do not interpret this as a strict
end-to-end model-call deadline. An over-budget returned reply stays recorded even
when it is not incorporated into a resolved history. As with the assembler,
trusted same-session provenance is a caller obligation, not authenticated by a
matching cursor or request string.

## Recorded-data controls

`results/pending-clock-01` archives the outcomes of replaying the previous
Inkscape clock/recovery reply and nine injected controls. The recorded reply needs
one read and reconstructs exactly raw events 2 through 11, including the intervening
sequence-2 observation. Gap, timeout, inconsistent cursor length, wrong echo,
interleaved command, invalid clock fields, transport exception, already-submitted
input and elapsed time budget all remain unresolved. The already-submitted case
performs zero reads; every other case here performs one. No command field occurs
in generated read requests and no continuation batch is returned.

These tests use recorded and injected replies, not a new live invocation. They
do not measure saved model round trips, inference latency, input tokens or cost.
Next run this explicit helper against a live historical-boundary episode, display
the retained history plus its newest referenced image, and review before issuing
any subsequent program. Frozen callers remain unchanged.

```text
python3 research/live_control/read_pending_clock_v1.py SOCKET ORIGINAL_CLOCK_REPORT.json --out NEW_DIRECTORY
```

The output directory must not exist. The probe script creates its archived cohort
exclusively; rerun in an isolated checkout with that cohort absent to avoid
overwriting measured results.
