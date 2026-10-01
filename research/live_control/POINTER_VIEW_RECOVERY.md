# Actual Inkscape recovery through reversible report views

The assistant tested the live view outside OpenTTD. After an observe-only program
advanced the observation sequence from 1 to 2, it deliberately supplied the initial
batch again for a Right-key program. The caller sent only a clock query and returned
`needs_reconciliation`, `program_sent: false`, `own command echo required`.

The direct cause matters: with the old cursor, the transport returned a previously
recorded clock boundary, before the new clock echo. The view preserved both the
new request identity and the old returned identity. This episode demonstrates
conservative handling of that historical boundary, **not a direct clock/observation
sequence-mismatch test**. The earlier mocked sequence test is still only mocked.

The assistant read from returned cursor 4 without a new command. That read returned
the intervening observe program and the pending own clock through cursor 12. Its
explicit sequence-2 image reference was inspected, even though it reused the same
PNG as sequence 1. Image-byte equality was not treated as sequence authority.

## Unplanned error retained

The next explicit program used `key` with `keys: ["ctrl", "s"]`, which is not the
backend's key schema. The runtime rejected the entire program with `unsupported
key`, before admission. The caller view preserved `program_sent: true` and
`unattributed_rejection`; sent does not mean admitted. No continuation batch was
issued. The original rejected steps and complete reports remain archived.

After inspecting the rejection and existing key schema, the assistant explicitly
concatenated the contiguous received records from cursor 4 through 16. This included
the rejection; no event was deleted. It corrected the save step to
`{"op":"chord","modifier":"Control_L","key":"s"}` and submitted a new
`corrected-move-save` program. This was a deliberate corrected attempt, not an
automatic retry. The latest known observation was still sequence 2; a clock query
does not create a new visual observation or prove that content is fresh.

The resulting image showed x=52, y=50, width=40, height=30, and the saved SVG and
independent legacy score agreed. The task was rightward movement with preserved
size/vertical position; this does not establish requested-distance precision.

## Audit and cost

`results/pointer-view-stale-01` contains a pre-run caller source manifest, runtime
source hashes, all requests/replies/views, original reports, frames and saved SVG.
`audit_pointer_view_stale_v1.py` verifies source hashes and round-trip restoration,
each reply against its exact raw-log slice, all 45 unique events covered by 53
received events including overlap, nine AIT/PNG reconstructions, and explicit
prefix reassembly including the rejection. Only `advance-observation` and
`corrected-move-save` were admitted. The first recorded physical input follows
the corrected admission, and both terminals verify release.

There were ten socket exchanges. Capture-to-independent-evaluation was
**118.15538916 seconds**, including deliberate stale input, read-only recovery,
schema mistake, inspection and correction. This is not a performance comparison.
Visible views were not truncated in this episode. The bridge process exited zero;
this older desktop entry point does not emit per-child structured cleanup proof.
Actual model tokens, costs and receipt timestamps remain unavailable.

## Practical caller examples

These are the existing v9 backend forms; the view layer does not normalize aliases:

```json
{"op":"key","key":"Return"}
{"op":"hold","keys":["Right"],"duration_ms":80}
{"op":"chord","modifier":"Control_L","key":"s"}
```

Inspect `state`, `reason`, request identity and retained replies before continuing.
On `needs_reconciliation`, do not infer admission from `program_sent`, automatically
reuse old coordinates, or resend input solely because a result boundary is missing.
The manual recovery here relies on the inspected v9 whole-program rejection and
complete local event history. It is not a generic automatic reconciliation policy.

Next: directly exercise sequence mismatch with an otherwise current receipt cursor,
and develop a bounded reconciliation read that preserves all intervening evidence.
Do not weaken the command-echo check to make historical boundaries appear current.

```sh
python3 research/live_control/audit_pointer_view_stale_v1.py
```
