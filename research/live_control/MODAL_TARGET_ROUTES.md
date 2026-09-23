# Keyboard and coordinate activation have different failure conditions

Eight scripted Linux/X11 Calc trials show that replacing Return with a click
fixes the known internal-focus fault but introduces dependence on geometry and
the actual hit target. Neither route provides semantic target identity.

## Matched task and retained results

Each session uses seed 991022, values 532/590 and the same source format dialog,
template, 250 ms proposal lifetime and ordinary two-second Executor lease.
`guarded_modal_backend_v3.py` binds the guard to the submitted first-step value
instead of hardcoding Return. Tested steps are Return and root-coordinate click
(785,463), the known fixture's Excel button center. There is no automatic route
selection, new target-handle API, or default runtime change.

After the visual guard passes, the probe interposes before ordinary execution:
no mutation, two Tab presses, dialog movement to (440,250), or a child X11 window
covering the Excel button. The six normal/focus/move cases were planned together;
the two occlusion cases were a subsequent planned cohort. All are
DEVELOPMENT_KNOWN, one trial per cell, with fresh isolated application sessions.

| Post-check condition | Return | Coordinate click |
|---|---|---|
| None | completed; XLSX saved | completed; XLSX saved |
| Internal selection changes to ODF | completed; XLSX unchanged; ODF Save as | completed; XLSX saved |
| Dialog moves | completed; XLSX saved | needs_decision; XLSX unchanged |
| Same-surface child covers button | completed; XLSX saved | completed; XLSX unchanged |

Independent XLSX reads find [532,590] on successful saves and [null,null] on
unsaved cases. The clicked occluding child receives X11 ButtonPress and
ButtonRelease events (types 4/5); Return produces neither. The retained after
image shows the format dialog still present with its Excel button covered.
This is direct evidence that a permitted client-surface descendant need not be
the intended application control. The synthetic child is test instrumentation,
not a measured naturally occurring app overlay.

The moved click fails the existing pointer checks before a pointer admission;
sampled pointer position is unchanged and no keys/buttons remain owned. Its
owner revision nevertheless advances 0 to 1: the owner increments revision for
attempted mutations before validating them. An initial audit incorrectly assumed
revision equality and failed. Reading input_owner_v9.py explained the mismatch;
the corrected audit checks pointer position, absence of pointer admissions and
released ownership. We do not claim revision counts physical input events.

## Verification and limits

`audit_modal_target_routes.py` verifies listed source hashes, all eight artifact
scores and workbook contents, time order, X11 binding changes, image predicates,
overlay event types, terminal release, and 15 exact AIT/PNG observation frames.
It records hashes of 24 diagnostic images and eight saved workbooks. Result
directories are `results/modal-target-route-01` and
`results/modal-target-occlusion-01`; consolidated audit is
`results/modal-target-routes-audit.json`.

Diagnostics and injected settling increase check-to-input latency; these runs
cannot establish natural race frequency, end-to-end assistant speed, or token
savings. The guard still samples before dispatch, is optional and private, and
uses display names rather than runtime incarnation. V3 shallow-copies a first
step; only flat scalar key/click steps were evaluated, not nested programs.
Its proposal describes the image, not an independently authenticated semantic
target. Listed hashes are not a complete transitive dependency manifest.

## Architecture consequence

Issue #45 revalidated target handles cannot be implemented as a cached coordinate
plus a top-level surface check and called semantic identity. Issue #34 effect
outcomes remain required for either input route. A route can improve one fault
axis and fail another; route selection should report its evidence and limits
(also relevant to Issue #51) rather than nominate a universal winning primitive.

Next use the same failure matrix to evaluate action-bound effect evidence with
VERIFIED, CONTRADICTED and UNKNOWN distinct from program terminal, then measure
actual assistant boundaries and time to recognized completion. Any later guard
or target change must retain both wrong-focus and same-surface overlay cases.
No broad route promotion or freeze credit follows from these eight trials.
