# Development and actual-use log

2026-09-13 JST. All work is local Python research; no runtime/release promotion.

## Actual assistant use → interface changes

The parent assistant used `dogfood.py` through a persistent terminal, opened the
receiver's reconstructed PNGs, and chose keyboard/drag/save commands itself.
The A1 scripted task controller was not called. Fixtures/setup and post-control
file oracles were reused. These are exploratory demonstrations, not randomized
model performance measurements.

1. `results/dogfood-calc-01`, seed 730101: blank sheet, A1=158, A2=389, preserve
   XLSX format and save. The assistant inspected initial, typed, intermediate,
   format-dialog and final images. First input returned an exact unchanged frame:
   the application had not repainted yet. An explicit next observation showed
   158. The final independent saved-file score was correct `[158,389]`.
2. Added a bounded change wait after streaming input acknowledgment. Metadata
   always says semantic completion is unknown. This removes the need for an
   extra manually requested observation when the first sample has not changed;
   it does not prove a speedup or completion. Command payloads are now logged.
3. `results/dogfood-inkscape-02`, seed 730201: the assistant inspected the red
   rectangle, selected it, inspected handles, dragged from (620,390) to (656,390)
   and saved. The first selection sample was unchanged; the same command's wait
   produced a selected frame. The final saved SVG independently had x=77.118645,
   y=50, width=40, height=30, no transform. Contract is movement right with shape
   preserved, not an exact pointer-to-document gain. An intermediate drag frame
   still showed partial motion, and the post-save image still had the old dirty
   title while the later X11 context did not. Separate timestamps were necessary.
4. Removed repeated PNG encoding for unchanged frames; retain a reference to the
   prior image file and still archive the small packet/new metadata. Early adapter
   PNG archival took about 34–55 ms/sample in the two demonstrations. This cost is
   recorded separately from codec/capture and was not part of A2 timing. The
   revised reuse path was subsequently exercised in XTerm, described below.
5. `results/dogfood-xterm-03`, seed790201: the unsupported `abc!` command was
   rejected before any input. The next exact unchanged observation reused
   `001.png`, with5.328ms archival versus31.328–43.161ms for new PNGs in that
   session. The assistant then entered/submitted `t790201`; the independent output
   was exact. This is one reuse-path demonstration, not a latency ablation.
   The adapter now reports its supported character set and rejects unsupported
   whole strings before the inherited driver can type a partial prefix.

Raw `.ait`, PNG, events and saved files are retained in each directory. Original
dogfood source was copied for both demonstrations. The first version did not log
command payloads or snapshot all inherited source hashes; it cannot support a
complete stand-alone trace replay claim. Later versions snapshot adapter/codec.

## A2 revision 1

Codec: 64-pixel tiles, exact pixel comparisons, full/reference/tiles, zlib level1.
It encodes both full and tile candidates and picks the smaller actual packet.
This provides a same-trace byte bound but costs additional local work.

Development `development-a2r1`: 16/16 successful episodes, 108 sampled frames
roundtripped. Its descriptive measurements are archived but not fresh evidence.
An analysis-only goal comparison was corrected to exclude ephemeral loopback
ports, and freeze-manifest checking was added before the fresh run. Neither
change alters the input/controller/codec.

Freeze `frozen-a2r1`; `fresh-a2r1-r1` STOPPED after 31 attempts, 30 successful.
Inkscape seed750103 O1 timed out after drag; the source/receiver image had not
moved, and independent SVG output remained x=50. All157 sampled images in the
failed episode reconstructed exactly. This is an input/control failure, not
evidence of corrupt tile transport. The whole fresh efficacy comparison is
rejected; do not combine its 30 successful episodes with a later revision.

Inspection of the final pre-drag frame showed all four selection handles. The
final frame and SVG were unchanged. Therefore a visible selection and 30ms press
dwell were insufficient in this extended local condition. App event consumption,
pointer-entry timing and scheduling remain possible explanations; none is proven.

## A2 revision 2

Keep A1 frozen files unchanged. A new shared Inkscape controller retains the same
semantic task and planned input events, but samples while the mouse button is
held and after every motion segment. It records every X11 event issue/ack and
still requires the public movement predicate. This is an observed segmented
gesture, not a proven adaptive motor controller: path points do not change based
on images. It introduces work deliberately to make the operation observable.

Old failed seed750103 regression: O1 and O2 both passed. This is development
evidence, not proof the rare failure is eliminated. New development/freeze/fresh
seeds are declared in [PROTOCOL.md](PROTOCOL.md). There are no silent retries or
failure deletions. Any new correctness failure again stops comparisons.

Revision2 development passed16/16 with138 exact frames. After freeze, both fresh
replicates passed32/32 each, giving64/64 and553 exact frames. The independent
archival analysis and final output rescore passed. See [REPORT.md](REPORT.md).

## Bounded Luna pilot

One Luna subagent produced the related-work note and read-only reviews while the
parent implemented and operated the GUI. Three external primary sources plus A1
were reviewed. Its first codec review identified two valid issues: negative tile
counts and ignored trailing compressed bytes. The parent fixed both and added
tests before freeze.

A later review repeated those issues from stale pre-fix contents. The parent
requested a fresh on-disk read; the reviewer verified current hashes and withdrew
the findings. An unsupported approximate elapsed-time claim was also removed.
The pilot was useful for bounded sourcing/review but required validation. No
controlled model comparison, wall-clock accounting, token cost or basis for
declaring Luna fastest/cheapest was obtained. Future review requests should carry
source hashes and require current reads, not remembered snippets.
