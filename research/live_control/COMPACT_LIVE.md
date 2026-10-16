# First live compact index use — audited

Fresh private Inkscape seed 206 used the same legacy move-right/save steps as the
paged episode. The original image was reviewed before input. The first compact
receipt reported needs_decision after one completed click step, with verified
release. The image remained unselected. The assistant inspected exact step/terminal
records; no Right input had been admitted. An attempted read of owner-events.json
before finish failed because the old fixture persists that file only at completion.

An explicitly reviewed new program `reviewed-recovery` used an 80 ms click, then
the same Right/save/settle steps. Its compact receipt bound the completed terminal;
the original image visibly showed x52, y50, width40, height30 and saved status.
Finish independently passed the SVG task and the bridge exited 0. The finish
request used the original cursor, so its saved reply includes overlapping recovery
history; only independent evaluation was presented at finish. Do not count duplicate
received history as new actions.

The final owner log confirms focus_changed during the first click, followed by
verified releases. The original interruption and failed diagnostic read are retained.
Both compact indexes and original images were visible without text truncation.
No full-report paging was needed, but this is an interrupted, unpaired episode.
It does not establish a causal speed or token improvement over paged-live-01.

Evidence is archived in `results/compact-live-01`. The audit verifies initial pinned
source hashes, runtime source hashes, original/index regeneration, image hashes,
all raw-history slices with overlaps, nine exact decoded frames and final SVG.
There are 42 unique events, 69 received records (27 overlapping), six socket
exchanges. The first index is 3194 serialized bytes; recovery index 3912 bytes.
Initial capture to independent evaluation is 91.421783 seconds. First interrupted
terminal to recovery admission is 50.594751 seconds, including diagnostic inspection,
commentary and preparation. These do not isolate model time or index performance.

`compact_recover_v1.py` was created before recovery but its persisted digest was
recorded only at audit, a weaker source attestation than the initial pinned plan.
The old fixture has no structured per-child cleanup report; bridge exit 0 was seen.
Reproduce with `python3 research/live_control/audit_compact_live_v1.py`.
Preserve measured
`compact_live_v1.py` and `compact_recover_v1.py`; do not rerun for a clean outcome.
Next identify whether interruption
cause can be provided in the ordinary terminal evidence rather than only at finish.
Do not alter frozen runtime files to add that cause without a new version/study.

Code inspection: the tested executor_v3 catches parameterless DecisionRequired and
emits needs_decision, then release_all's final release record. Earlier asynchronous
owner focus_changed release is retained separately in owner-events.json. This
explains the missing causal detail in this terminal; it does not justify reading
the globally last owner event as the cause of a later intent. Inspect newer runtime
versions before adding a new mechanism, and preserve intent attribution if extended.
