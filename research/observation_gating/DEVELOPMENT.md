# A1 development record

All runs below are development evidence. None is pooled into the fresh result.
The initial local session began on 2026-09-12 JST and crossed midnight into
2026-09-13 JST. Machine-readable environment timestamps are UTC.

## Retained failures and excluded evidence

### Xvfb pathname readiness — rejected

`results/baseline-screen-01/` stopped on the first XTerm baseline attempt before
the app launched. The inherited XSession waited for `/tmp/.X11-unix/X120`.
WSLg's shared socket directory prevented creation of a pathname socket, while
Xvfb was listening on the Linux abstract UNIX socket and accepted X11 clients.

Fix: wait for a successful X11 handshake, and close process groups if session
initialization raises. The original failure JSON and stop record remain saved.
The Xvfb process left by that initial failed constructor was identified by its
PID and exact command line and terminated. No user display was replaced.

`results/baseline-screen-02/` then passed one O0 task for each app (4/4).

### Accepting a mapped but unpainted Calc window — excluded

`results/development-01/` passed 32/32 scripted tasks and reconstructed every
sample exactly. However, visual inspection of its retained PNGs showed that
Calc often displayed an empty grey client area while already accepting the
queued inputs. Its final saved workbook was correct, but counting repeated
startup-grey frames overstated redundancy for an already usable worksheet.

The entire paired development screen is excluded from efficacy claims. This
is a baseline/readiness confound, not a failure of the exact equality operation.

Fix: before starting task timing, require a visibly painted Calc worksheet.
The development heuristic is more than 20% near-white pixels and more than
128 colors, with a 15 s deadline. It applies equally to both strategies and is
never used for image gating. Setup capture counts are saved separately.
`results/baseline-painted-01/` passed, and manual inspection confirmed a visible
grid before input and the correct entered values afterward. This readiness
heuristic is scoped to the blank-sheet fixture, not promoted as a universal
application-ready detector.

### Calling fresh-image receipt semantic completion — rejected

A screenshot or an unchanged-image reference can arrive before the app visibly
consumes input. The experiment therefore records input acknowledgment, fresh
observation receipt, first changed visual/context feedback, and known public
effect separately. Final saved-output correctness is measured after controller
return. Actions without an observed change keep a null changed-feedback time;
they are not assigned zero latency or assumed complete.

### Raw version diagnostics as environment identity — repaired before freeze

Inkscape's `--version` emitted a timestamped GTK warning on stderr. Including it
in the version string would falsely label fresh replicates as different app
versions. Stable stdout versions are compared; stderr remains in separate
diagnostic metadata. This does not change the measured task/controller.

## Accepted development screen

`results/development-painted-02/`: seeds 1201–1204, four pairs/app, 16 pairs,
32 live episodes, O0 then O1. All task, input schedule and exact reconstruction
checks passed. Counterbalanced order is reserved for the fresh evaluation.

Independent PNG audit and pair bootstrap:

- Task success: O0 16/16; O1 16/16.
- Same-trace image reduction: 20.50%, 95% pair-bootstrap interval 10.36–31.60%.
- Live-run image-count reduction: 23.14%, interval 10.57–35.09%.
- Paired median local task wall difference (O1 minus O0): -5.03 ms,
  interval -11.01 to +8.87 ms. This does **not** establish a latency win.
- XTerm had no repeat images in this short task. Exact suppression is correctly
  a no-op when every sample differs; no idle frames were inserted to improve it.

The summary is in `results/development-painted-summary/`. Source hashes in this
development directory predate metadata/freeze bookkeeping changes only. The
controller, input parameters, readiness rule and gate used by the accepted
screen are those frozen for A1.

## Freeze

`results/frozen-a1/` contains the protocol, Python source copies and SHA-256
manifest captured before fresh seeds were run. The fresh runner rejects changed
source, parameters or app/dependency versions. Fresh results must be assessed
under that manifest and may not be combined with a later tuned implementation.

## Revision 1 fresh evaluation — INVALID, baseline failure retained

`results/fresh-a1-r1/` stopped after 10 attempted runs, with nine task successes.
The failed run is `inkscape-91026-O0`; O1 had succeeded first in this pair. O0's
`drag_right` public-effect wait timed out. All 165 sampled images in the failed
run were reconstructed exactly, so this was not an observation-gate failure.

The pre-drag PNG shows the rectangle with **no selection handles** after Ctrl+A.
The first post-drag PNG shows a selected but unmoved rectangle. The last frame
still shows x=50 in the visible toolbar. This supports the diagnosis that XSync
input delivery plus the next screenshot did not establish selection consumption
before the dependent drag. A known input-delivery policy is not enough to prove
every application precondition.

Revision 1's planned second replicate was not started, and no partial image or
latency result is promoted. Its manifest, source snapshot, protocol, observations,
action timings, failure and stop record remain unchanged. This revision's failure
path did not copy the unsaved SVG before deleting temporary application state;
the PNGs and controller exception are retained, and revision 2 repairs artifact
preservation on error as well.

Revision 2 adds a common visual selection barrier: find dark selector handles on
all four sides of the acquired red target, then drag. It never gates an image and
uses no saved-file oracle or fixed app coordinate. The failed seed is now a
development regression, never fresh evidence again. Re-freeze and use new seeds
only after renewed development validation.

## Revision 2 development and freeze

- `regression-selection-01`: the failed seed 91026 passes both O0 and O1 after
  the common selection barrier. It is explicitly development data.
- `development-selection-long`: 12 additional Inkscape pairs, seeds 2201–2212;
  24/24 task successes and no image reconstruction error.
- Inkscape's initial visible-target wait is also moved into setup so repeated
  startup-grey images cannot contribute to task image reduction. This makes its
  task timing boundary consistent with Calc's painted-document boundary.
- `development-a1r2-final`: four pairs per app, seeds 1301–1304, 32/32 successes;
  this is the final controller/readiness/gate version. Same-trace image reduction
  is 18.57% (95% pair-bootstrap interval 10.50–28.07%). Live-run count reduction
  is 20.17% (8.82–32.17%). Paired median task-wall delta is +0.78 ms
  (-7.15 to +9.22 ms), so latency remains unproven.
- `frozen-a1r2`: source, analyzer, protocol, parameters and dependency versions
  are snapshotted after these development screens, before fresh seeds
  290101–290112 and 390101–390112. No revision 1 runs are pooled with revision 2.

## Revision 2 fresh evaluation — INVALID, selection barrier insufficient

`fresh-a1r2-r1` stopped after four attempted runs (three successes) when
`inkscape-290102-O0` failed to move the rectangle after its drag. O1 had succeeded
first in the pair. This time the pre-drag images showed selector handles, and
the retained SVG still had x=50, y=50, width=40, height=30. The image audit passed
for all 165 samples, including the timeout. No revision 2 efficiency claim is
accepted and its second replicate was not started.

This falsifies **selection verification alone is a sufficient repair**. It does
not isolate the exact internal Inkscape cause. Delayed press/drag consumption is
a competing explanation, especially since the old 5 ms input policy was measured
on a different Debian environment and the successful development runs always
put O0 first. A fresh run must not be counted as success simply because its gate
is lossless.

Revision 3 tests a conservative 30 ms press-to-motion dwell and counterbalances
pair order in development too. It retains the public movement check, makes no
claim that a dwell is a completion guarantee, and requires another development
screen and fresh freeze. Previous failed revisions remain in the evidence ledger.

## Revision 3 development

- `development-dwell30-balanced`: 12 Inkscape pairs, 24/24 successful tasks with
  alternating pair order. The 30 ms dwell is a conservative local delivery policy,
  not a claim of optimality or universal sufficiency.
- `regression-dwell30`: seed 290102 succeeds in both strategies in O1/O0 order.
- `development-a1r3-final`: 16 balanced pairs over four apps, 32/32 successes and
  exact archive reconstruction. Same-trace image reduction is 18.22%
  (95% pair-bootstrap interval 10.64–26.83%). Live-run count reduction is 21.67%
  (12.28–31.82%). The paired median task-wall delta is -9.52 ms
  (-21.56 to +6.68 ms), again not a demonstrated latency improvement.
- `frozen-a1r3`: the tested control/input/readiness logic, gate, analyzer,
  final protocol and versions are frozen before seeds 490101–490112 and
  590101–590112. Revision 1/2 failures remain excluded from efficacy estimates
  and included in the overall research record.
