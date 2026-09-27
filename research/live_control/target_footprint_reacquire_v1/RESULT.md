# Bounded target footprint reacquisition — retained container outcome

## Disposition

**PASS_SCOPED_CANDIDATE**, not shared-runtime promotion. The first and only 30-case local Inkscape/Xvfb allocation completed. Candidate condition-correct outcomes: 15/15; center-patch comparator: 6/15. Model calls: 0. No DOOM episode or stage-clear claim.

Public pre-run freeze: `993fb66cafef19f0f32dc6dd77833348d5d679a6`.
Executed source publication: `3dde40385d6b8a171a1341c666699c1a7ca26415`.
Runtime source remains the verified offline base `9e6d5ecd`; publication base is `c6d1954`.

## What the experiment tested

PR #326's target revalidation used the 11x11 interior around a reprojected point. A circle and a same-color square can have identical interior pixels. Both arms here require TWO fresh target observations. The candidate instead checks the observed outline-containing footprint, searches within 120 pixels of the coarse scene projection, and refuses a spatially distinct alternative matching appearance. Its repeated position must remain within 2 pixels; maximum current observation age is 0.5 seconds. Every click still goes through ordinary InputOwner v10 admission and release.

The reference target point/crop are fixture-authored from visible pixels, not model-authored. Reference and current documents are separately opened and explicitly rebound. Source imagery supplies no input authority. The controller neither reads the persisted-SVG scorer nor accesses document structure. This is process/code-path separation in a shared container namespace, not filesystem isolation or a security proof.

## Independently scored results

Three scene seeds (1841,1842,1843), signed pan counts (-4,+3,+6), alternating arm order, five scenarios per seed. Every case uses a private display/profile and disposable document. All 30 planned cases ran once; failures were not retried.

| Scenario | Center patch | Full footprint | Required result |
|---|---:|---:|---|
| Stable after pan | 3/3 | 3/3 | Delete/save target only |
| Moved target plus square at old point | 0/3 | 3/3 | Retrieve circle, preserve decoy |
| Same-color square replaces removed target | 0/3 | 3/3 | No task input; exact file unchanged |
| Missing without substitute | 3/3 | 3/3 | No task input; exact file unchanged |
| Duplicate matching appearances | 0/3 | 3/3 | Refuse ambiguity; exact file unchanged |

The comparator deleted a wrong object in SIX cases. Three additional duplicate cases deleted the original target but violated the frozen ambiguity-refusal policy; these are not labelled wrong-object deletion. Candidate: all six positive edits correct, all nine negative/ambiguous cases refused, wrong deletions zero.

The independent scorer checks saved SVG after controller return: removal of only task-target, preservation of all other renderable objects and canvas attributes, or exact unchanged bytes plus no task input for negatives. A controller PROGRAM_COMPLETE flag never replaces this oracle.

Fourteen of fifteen paired initial current images were pixel-identical. One stable pair differed at 414 pixels and both arms passed; the discrepancy remains in the archive.

## Retention and verification

The frozen audit reclassified every target gate from raw PNG pixels and recomputed SVG outcomes: 96 controller images, 48 target gates, 18 clicks, 36 task key operations, and 514 verified-empty release records including setup/close. These are records, not 514 independent reliability trials. Eight resolver tests and py_compile passed before the allocation. Nine Python source blobs plus prereg.json match the executed bytes on GitHub (10/10).

The full archive was re-extracted to another directory: all 812 manifest-listed files verified; the scientific audit reproduced byte-identical JSON; all eight unit tests passed again. The archive has 813 entries including its manifest.

Three development probes are retained separately and excluded from the measured denominator. A terminal streaming interface was unavailable before any allocation output existed; the unchanged frozen runner was then launched once as a local subprocess and monitored to completion. No case was consumed or retried at that boundary.

## Browser transfer — blocked, no controller execution

A separate Chromium 144 development probe displayed `127.0.0.1 is blocked` with an organization-policy notice. Readiness timed out before the target controller ran; no POST receipt exists. Policy was not changed or bypassed. Source, stderr, screenshot and empty receipt file are retained in the full archive. No successful browser transfer is claimed.

## Environment and costs

AMD EPYC 9V74, five available/affinity CPUs, unpinned frequency; Linux 6.18.44/glibc 2.41. Python 3.13.5, OpenCV 4.13.0 with one OpenCV thread, NumPy 2.3.5, Pillow 12.3.0, python-xlib 0.33, Inkscape 1.4, Xvfb 21.1.16/Openbox. One case at a time; batch one RGB frame.

Full-footprint evidence computation median 8.769 ms, range 8.268–11.061 ms (21 gates). Center computation median 0.120 ms, range 0.101–0.200 ms (27 gates). These exclude capture/PNG persistence/startup. Counts differ because rejected cases stop early. No whole-process causal speedup is claimed: one arm may correctly refuse where the other wrongly edits.

## Evidence boundary and limitations

See EVIDENCE.json for the exact ZIP size/hash. The GitHub checkout contains frozen source/schedule, report and compact outcome data, NOT the raw PNG/SVG tree. Full retained replay requires the conversation evidence ZIP. It also includes the six-file verified runtime-source closure; external Python/system libraries are not bundled. Replay: `python -m unittest -v test_resolver.py`, then `python audit.py results` from the extracted experiment directory. Never rerun into the retained output path.

The patch is an appearance reference, not proof of semantic identity. Same-looking object replacement, post-click selection interference, scaling/themes, motion during processing and targets beyond the search radius remain open. This study does not address Issue #327's paint-lag race. Source/thresholds are not promoted into a shared runtime. Relevant transfer hypotheses: GUI target rebinding, robotic visual tracking, and guarded cache reuse; only this Inkscape fixture has live outcome evidence here.
