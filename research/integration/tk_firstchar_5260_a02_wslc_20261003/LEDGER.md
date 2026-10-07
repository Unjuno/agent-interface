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

Task 1: complete; private image and exact runtime versions/receipts retained.
Task 2: complete; final frozen source construction suite17/17 before input.
Task 3 first outcomes: candidate138.1676s, auditor64.5092s, both once/exit0;
96 rows,65 exact/31 nonexact; auditor PASS_AUDIT/errors[]. CPU released.
First retained cross-file checker FAIL: all96 ready_binding errors; all15
corruptions rejected. No formal rerun occurred. Additional custody tests
RED6 then GREEN6; explicit STOP packaging test RED before implementation.

Ruling: overall qualification is STOP_READINESS_CUSTODY_AFTER_PASS_AUDIT —
the stronger post-outcome check exposes overwritten readiness epochs;
do not normalize data or repair frozen sources to make it pass — cost if
wrong: conservative loss of a formal claim, not loss of first evidence.

Ruling: integrate an explicitly expected negative-evidence packet, not a
scientific PASS — exact96 readiness errors must remain and any other
custody failure still fails validation — cost if wrong: misleading packet
acceptance; original checker/source/streams plus regression test guard it.

Retained validation: PASS_RETAINED_STOP_PACKET,669 manifest files,
all15 corruptions rejected,96 readiness failures explicitly retained,
zero formal commands. Package tests24/24; workspace tests22/22;
committed-tree index156 directories; git diff --check passed.
Final review: self-review; no new review subagent was authorized.
Important finding (readiness epoch) is not fixed in consumed sources:
overall STOP and first failing verifier are preserved for a fresh A03.
No product/runtime code or original study path is changed.

Deferred minor: inherited audit delay_ms arrays are empty; exact clock
brackets remain in raw and no quantile/speed claim is made from those arrays.

Ruling: execute inline without repeated user approval — explicit human
direction says continue autonomous experiments through roadmap completion —
cost if wrong: unneeded local bounded experiment, not user-desktop input.

Ruling: coordinate derivations are not window-identity treatments —
actual candidate calls XTest without addressed ID — cost if wrong: reduced
claim scope, no discarded observations.
