# SDD ledger — plan: tk_firstchar_5260_a02_wslc_20261003/PLAN.md

Pre-flight: Task 1 produces a pinned image and host receipts consumed by
Tasks 2/3. Task 2 produces sources and corruption tests consumed by Task 3.
No source from another agent is modified.

Ruling: reuse the already isolated clean clone on a new additive branch
instead of creating another checkout — current workspace is a private
research clone, not the user's shared checkout — cost if wrong: branch
collision; latest #5260 open PR/branch searches both empty.

Task 1 host capture: RED 3/3 missing implementation; the draft literal
SHA was corrected using independent .NET SHA256 over bytes
114,97,119,0,111,117,116 before the first GREEN run.

Task 1 receipt tests GREEN 3/3. Image build01 started
2026-10-03T12:23:36.968249Z and finished 12:25:02.713287Z, exit 0;
85.745 seconds is one build's host wall time, not a performance comparison.
The initial Docker-style Go-template inventory command was unsupported;
a corrected JSON filter during build returned no tag. No tag replacement
or global configuration change was requested.

Task 2 audit tests RED: baseline changed bytes, false baseline byte count,
false first-frame byte count all passed the old gate incorrectly (three
failing controls). Source corrections remain in this additive path only.

Task 2 construction smoke01: candidate exit 0, one exact hxy save,
baseline hash/byte integrity 1/1; auditor exit 2 with image_crop_tool.
The inherited auditor attempted its crop inside read-only candidate input.
Retain this first outcome; a corrected raw-only construction audit uses its
own derived directory without another candidate input trial.
Xvfb and Openbox warning logs are retained, not hidden.

Task 2 corrected raw-only smoke01 audit exit 0, errors empty; OCR unresolved.
Smoke02 (new bounded busy/0ms construction input, NOT formal) candidate
and auditor both exit 0. Target saved xy; decoy received h before target
FocusIn, worker spans all key dispatch. This is retained construction
observation, not pooled into formal 96 rows. Empty OCR was labelled MATCH
by the inherited label despite visual-success count 0; two new RED tests
pin empty OCR rejection and frozen raw source binding before correction.

Task 2 source-hash and worker-clock tests RED then GREEN; 15 tests passed.
Do not infer an effective CPU/memory limit from requested flags.

Ruling: execute inline without repeated user approval — explicit human
direction says continue autonomous experiments through roadmap completion —
cost if wrong: unneeded local bounded experiment, not user-desktop input.

Ruling: coordinate derivations are not window-identity treatments —
actual candidate calls XTest without addressed ID — cost if wrong: reduced
claim scope, no discarded observations.
