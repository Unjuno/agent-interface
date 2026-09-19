# Desktop pointer transfer and drag precision — 2026-09-13

`interactive_v11.py` exposes the existing candidate `session_v9` to the existing
desktop fixtures. No backend semantics changed and pinned v10 stays unchanged.
One assistant visual Inkscape episode selected, dragged and saved a rectangle;
the saved SVG passed the legacy rightward-motion/size/vertical-position contract.

That success does **not** establish accurate requested displacement. The assistant
requested a 24-screen-pixel path, but the SVG moved from x=50 to x=60.169491 at
118% zoom, approximately 12 screen pixels. The old task deliberately requires
only rightward movement, not exact motor gain. This gap is now recorded rather
than treating the legacy score as evidence of precision.

## Evidence

Inkscape 1.2.2 (b0a8486541), private Linux/Xvfb/Openbox, unchanged shared backend,
fresh fixture/profile per episode. The assistant pilot is `results/pointer-desktop-01`.
It contains eight exact observations, three accepted programs, and one rejected
program: the assistant supplied `mod` instead of the API's `modifier` field.
Whole-program validation rejected it before the preceding drag could execute.
The corrected program was submitted separately. This is an API discoverability
problem to address, not an omitted failure or successful first attempt.

The image immediately after clicking did not yet show selection handles; a later
explicit observation did. A subsequent pixel-quiet wait finished after three
samples/190.6 ms. Neither input acknowledgement nor pixel quiet itself proves
the document task is complete; final saved-file evaluation remains independent.

Two scripted pairs then compared paths with the same start/end and 200 ms declared
duration, deriving the starting point from the visible rectangle. Each selected
the rectangle and waited for bounded pixel quiet before dragging. They used the
same saved-file evaluation, plus a declared ±1 screen pixel displacement check.

| Order/cohort | Path points | Requested movement | Observed movement | Precision check |
|---|---:|---:|---:|---|
| 01 first: coarse | 3 | 24 px | 12 px | fail |
| 01 second: dense | 25 | 24 px | 20 px | fail |
| 02 first: dense | 25 | 24 px | 19 px | fail |
| 02 second: coarse | 3 | 24 px | 12 px | fail |

All four legacy scores pass and all four precision checks fail. Dense motion is
not an adequate fix, and its two outcomes differ. This small reversed-order study
does not isolate application event coalescing, drag thresholds or scheduler effects.
The Inkscape project documents a
[click/drag threshold](https://wiki.inkscape.org/wiki/index.php/PreferencesDialog),
which is a plausible mechanism to investigate; the exact cause in these runs is
unproven. Do not apply a hard-coded compensation to the shared interface based
on these numbers. The application preferences were not altered to make tests pass.

`audit_desktop_pointer.py` verifies the pilot's source manifest, both probe source
hashes, all 53 AIT/PNG reconstructions, completed-program release records, the
retained prevalidation failure, and saved SVG fields against evaluation records.
The four scripted sessions also recorded all owned processes exited. Their full
transitive source hashes are inherited from the unchanged pilot sources and were
checked at audit time, rather than independently captured in each pair's plan.
The pilot entrypoint predates structured process-cleanup reports; its process
returned successfully, but it does not have the pairs' per-process cleanup record.

## Next decision

The shared pointer owner successfully routes through an active top-level window
whose focused child has a different XID, then executes click/drag and keyboard
save. OpenTTD and Inkscape now expose distinct shortcomings: placement boundaries
and application drag response. Cursor coordinates and object displacement must
remain separate quantities in both results and control logic.

Priority is feedback during bounded manipulation, useful post-action observation,
and a discoverable operation schema, followed by fresh task/geometry tests. More
pointer samples alone do not establish accuracy. No model-speed, token reduction,
runtime promotion or freeze qualification is claimed. The earlier hand-made X11
fixture startup fault remains unresolved; this turn shifted to the real-app
precision failure after discovering it and did not fix that startup fault.

```sh
python3 research/live_control/audit_desktop_pointer.py
python3 research/live_control/interactive_v11.py --app inkscape --seed 991003 \
  --out research/live_control/results-local/new-desktop-pilot
```
