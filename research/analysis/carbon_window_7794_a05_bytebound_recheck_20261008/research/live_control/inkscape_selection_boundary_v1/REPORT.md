# Ordinary Inkscape: selection can change after visual revalidation

Decision: **RETAIN_ORDINARY_APP_SELECTION_BOUNDARY**. In this installed, unmodified Inkscape path, an accepted Right-key edit follows current selection, not the object selected at the earlier visual check. This is an Agent Interface contract boundary, not an Inkscape input-delivery defect or a universal impossibility claim.

Issue #333; task INKSCAPE-SELECTION-BOUNDARY-20260916-013. Publication base `3c6f07f0660aee854d6b2d2d0f525fd9f451de68`; freeze commit `cdd9a345110aee33a81086e56f8321ecd5903b7f`. Only a new research directory is added. No shared runtime, workflow, earlier allocation or user document is changed.

## Hypothesis and exact scope

Merged PR #277 demonstrated a semantic check/effect gap in a custom Tk app. This successor uses ordinary Inkscape 1.4, not a custom effect endpoint. A disposable SVG contains red rectangle A and blue rectangle B. The desired edit is one +2 SVG-user-unit horizontal nudge of A, with B and both rectangles' other geometric attributes unchanged.

The byte-identical existing `inkscape_red_target_planner_v1.py` and `inkscape_selection_scorer_v1.py` first validate A's solid red geometry and visible selection handles. A 2000 ms Lease binds the observed X focus. Only the predeclared selection trajectory varies; one measured Right press is admitted by unchanged `InputOwner v10`, released, and the document saved with ordinary Ctrl+S. Setup and context changes are OS XTEST clicks/keys; there are no application command/extension APIs. Saved SVG inspection is offline evaluation, never an action-selection input.

This is a standalone InputOwner composition probe, not an execution of the full latest Executor/caller stack. The inherited planner's pointer-click suggestion is used for initial selection only; the declared measured action is Right. A pre-edit screenshot is retained for diagnosis but is not read by admission. Physical focus is checked again, so same-window selection changes are deliberately isolated from focus changes.

## Frozen design and conditions

Twenty first cases, five per trajectory, serial fresh Inkscape/profile/private Xvfb per case. Schedule and source hashes were published before measurements in #333 comment 5691381864 and the freeze commit. The first duplicated hash token in that comment is explicitly corrected inline and in FREEZE.md; the underlying source bytes never changed after freeze.

CPU: AMD EPYC 9V74, shared host, affinity 0..4, frequency not pinned. CPython 3.13.5; Linux 6.18.44; Inkscape 1.4 (e7c3feb100, 2024-10-09); Xvfb 1100x800x24; python-xlib 0.33 from a retained wheel; Pillow 12.3.0; NumPy 2.3.5. Batch size one. Requested Right dwell 20 ms; Lease 2000 ms. Model/game calls zero. The source bundle hash and executable identity are in environment.json.

The SVG has width 300, height 200 and viewBox 0 0 300 200. Thus reported coordinate differences are SVG user units corresponding to the document's pixel units, not display pixels or physical metres. Absolute geometry tolerance is .001 user unit. Time uses one local monotonic clock; integer nanosecond differences divided by 1,000,000 have units of milliseconds. Reported clock resolution is not scheduling accuracy. No calibrated combined uncertainty or coverage factor is asserted.

## Results

| Selection trajectory after valid A check | Cases | A horizontal change | B horizontal change | Intended A-only edit |
|---|---:|---:|---:|---:|
| Stable A | 5 | +2 in all five | 0 in all five | 5/5 |
| Switch A to B | 5 | 0 in all five | +2 in all five | 0/5; five wrong-target edits |
| Select B, then reselect the same living A | 5 | +2 in all five | 0 in all five | 5/5 |
| Unrelated pointer movement without clicking | 5 | +2 in all five | 0 in all five | 5/5 |

All 20 initial A selection checks passed. All 20 measured admissions occurred before their original Lease deadline with unchanged X focus. Owner release was verified 20/20; complete keymaps and button state were empty before/after/final checks; all applications exited normally. Saved y/width/height stayed unchanged. Separate offline checks also confirm preserved document geometry, exactly the two rectangle objects, and unchanged fills.

The A-B-A case is **not** the incarnation-replacement ABA from #277: no object was destroyed or replaced. Returning selection to the same living A legitimately restores this nudge's target. Treating any intervening selection change as permanent invalidity would add unnecessary refusals here.

## Offline diagnostic, not a tested repair

A separate post-measurement pixel audit re-evaluates the retained images. A remains the same solid red region in all 20 pre-edit frames; appearance/coordinate identity alone would miss selection transfer. Four-sided selection handles identify B in all five switch cases, and A in the other 15. This supports a candidate selection-specific recheck, but no such new online guard is claimed tested in this block. Another check would still only establish its own observation-time condition.

Diagnostic recheck-finish to input-admission intervals, milliseconds (median; observed min-max): stable 168.101 [166.775,174.895]; switch 195.003 [193.179,201.884]; same-object return 360.026 [358.766,365.168]; unrelated 170.104 [167.602,172.864]. These include deliberately scheduled mouse interactions, waits and diagnostic capture. They are **not** spontaneous-race incidence estimates or comparative runtime-speed benchmarks. The study demonstrates a possible ordered interleaving, not its natural frequency.

## Failure retention and ERROR CHECK

One construction attempt exited before input because this installed version does not support the attempted --new-instance option. Its original driver and logs remain retained. The supported ordinary invocation was used for four subsequent construction cases, all excluded. All 20 measured cases completed once; no timeout, rerun, replacement or parameter adjustment occurred in the measured block. No experimental process remains running.

The pre-frozen independent-code auditor imports neither InputOwner nor the target selector. It re-derives movement from saved SVGs, verifies schedule, capture hashes/brackets, event order, physical keymaps, owner release, focus and normal exit. It returns PASS_BOUNDARY_AUDIT. Additional offline pixel/shape checks return PASS_POSTHOC_AUDIT. Eight separate corruption controls are rejected: false release, held key, expired admission, different focus, fabricated effect summary, corrupt image, duplicate measured request, extra object. This is checking code in the same session, not an independent agent review.

## H / T / D / C / U

H: revalidated selection is not carried as an expected-object condition inside a generic Right key.
T: fixed 20-case ordinary-app experiment, independent SVG scoring, pixel diagnostics, 8 corruption controls.
D: retain the observed ordinary-app boundary; no shared-runtime/production promotion.
C: current-selection editing is normal app behavior. A final selection check may catch a change that already happened; natural context changes may be rarer or rejected in other application paths. A broad epoch guard can unnecessarily reject same-object return.
U: deliberately inserted context change, one application/version/fixture/host, five repeats per trajectory, no model, no actual competing human process, no arbitrary semantic identity or atomic effect claim.

Next single question: on this same ordinary app, can one selection-specific check immediately before admission reject an already-changed B selection while allowing unrelated pointer movement and return to the same A, without claiming to eliminate changes after that last check?

## Retention and replay

The GitHub compact archive contains exact measurement records, event/owner logs, before/after SVGs, executable sources, preregistration, environment, audit outputs, retained construction diagnostics, and **40 lossless selection-region crops** (recheck/pre-edit for each measured case). COMPACT_MANIFEST.json binds every included file and original pixel crop coordinates. Full-screen PNG hashes there are provenance only: the full original PNGs and generated application profiles remain in the separate downloadable complete archive. Do not describe the compact projection as retention of every full-screen byte.

After verifying and extracting the compact archive, `python compact_audit.py .` rechecks its independently auditable scope. The complete archive additionally supports `python audit.py .` and `python posthoc_audit.py`. Verification does not start a GUI. Fresh live reproduction requires a new allocation/output directory, the recorded Python/X11 dependencies, and the separate upstream wheel bundle; never rerun a consumed measured directory.

Official behavior reference: Inkscape's keyboard reference, maintained at https://gitlab.com/inkscape/inkscape-docs/documentation/blob/master/keys/keys.xml, documents arrow-key movement of selection and the default 2 px nudge. The numerical conclusions above come from the retained saved SVGs, not from that documentation alone.
