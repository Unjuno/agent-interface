# Bounded received-history assembly

`received_history_v1.py` replaces the manual JSON concatenation used in the
[Inkscape recovery](POINTER_VIEW_RECOVERY.md) with an offline checked operation.
It accepts received request/reply slices in encounter order, checks cursor lengths,
requires a contiguous covered interval, and permits overlapping records only when
their serialized JSON values agree. It retains every unique event, including
rejections, and each slice's complete request and non-record reply metadata.

The result is `assembled_review_required`, with a `review_batch` and slice
descriptors. It is not permission to continue input. There is no socket access,
input submission, retry, lease refresh, task-success inference or new image.
Callers must establish that slices belong to one trusted runtime session; cursor
agreement alone does not authenticate session identity. The assembled records can
be passed to the existing image selector with an explicit run directory, but that
selector's historical-image authority restrictions remain in force.

Limits are 32 slices, 256 unique records, and 8 MiB serialized input. The CLI also
bounds its file read to 8 MiB plus one detection byte. Missing records, conflicting
overlap, unresolved statuses and exceeded capacities cause failure rather than
discarding evidence. `unattributed_rejection` is allowed as preserved evidence;
its status remains in the slice descriptor and is never rewritten as success.
Other transport statuses, including timeout/gap, are not assembled by this version.
This is a data-size bound, not a hard processing-time or model-output-size guarantee.

## Recorded-data validation

`results/received-history-01` retains seven actual slices through the rejected
save-key attempt from `pointer-view-stale-01`. They assemble to the first 16 raw
events, preserving the unsupported-key rejection and overlapping historical clock.
The probe reconstructs each original reply and request from the assembled form.
Ten negative controls reject missing intervals, inconsistent overlap, boolean
cursors, length mismatch, timeout, gap status, record/slice capacity excess,
non-object records and nonfinite JSON values.

This is offline validation against an actual episode, not a new live recovery,
direct sequence-mismatch test or a measured reduction in model round trips/tokens.
The next live step is to use this assembly when reviewing received slices and test
sequence mismatch separately with a current receipt cursor. A future bounded
read-only drain must preserve evidence and handle timeout/gap explicitly; this
helper does not implement that network policy.

```text
python3 research/live_control/received_history_v1.py SEGMENTS.json --out NEW_OUTPUT.json
```

The input is an array of objects containing `request` and `reply`. Output creation
is exclusive so an existing result cannot be silently overwritten. The probe
script creates the frozen `results/received-history-01` cohort exclusively; reruns
require an isolated checkout with that output absent, preserving the archived run.
