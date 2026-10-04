# A12 file task and explicit recovery — preparation, not formal evidence

New question under open #5260, extending A11 actual drift and closed #4134's
same-run effect distinction without replaying any prior allocation.

H: after observed drift causes no-input refusal, one explicitly requested
recovery click and a NEW post-click target ACK can permit one task attempt
that saves exact target text to an independently readable file. The old
admission does not transfer; failed fresh observation stops without typing.
T: proposed fresh private Tk sessions, stable baseline vs bounded explicit
recovery vs no-recovery refusal, with new literal payloads and geometry
conditions. Retain all click/admission/drift/recovery/input/Save/file events,
app-process boundaries and first useful visual frames. No automatic replay
of partially emitted text. Concrete six/eight-cell schedule not frozen yet.
D: method custody and task correctness remain separate: a faithfully saved
wrong value is a finite H_FAIL, not repaired into PASS. Source, commands,
criteria and complete independent audit must be frozen before GUI invocation.
C: private single-container WSLc CPU, source/input RO, no network/model/GPU/
user display or existing-run mutation. No new formal allocation claimed yet.
U: not same-model heldout efficacy, physical release, ordinary uninstrumented
app generality, population reliability, human tempo or crash durability.
File fsync is an observed cooperative operation, not a crash-recovery proof.

TDD construction: initial4tests RED because save_once missing; implementation
passed4 actual filesystem tests. Independent checker4tests initially RED
because file_errors missing, then implemented without importing producer.
No Tk/candidate/XTest/GUI experiment launched. Preparation-only files outside
repository; original A11 and closed predecessor records remain unchanged.
Windows8 testsPASS and pinned WSLc Linux8 testsPASS (file-unit01 exit0).
The Linux run exercised real temporary filesystem writes/readback/exclusive
second-save rejection and independent copied-content checks, not GUI input.
Existing host swap-limit warning persisted; effective caps unproven.

Recovery increment: six tests first failed because RecoveryAttempt was absent.
Added one explicit per-instance attempt, only after observed-drift refusal
and zero prior Key/Save. It performs one targetclick, waits on real OS pipe
for a post-click bound target ACK, requires sequence later than the observed
drift, then emits payload/Save once. Timeout consumes the attempt; old ACK,
old sequence, absent request, partial input and invalid refusal emit nothing.
Caller dictionaries are not authenticated authority; independent audit needed.

First combined Windows14 run had one test expectation failure: an old frame
and new click shared an equal monotonic clock tick, so common gate admitted
but recovery sequence guard rejected emission. Linux14 passed. The test now
uses an explicitly earlier event timestamp for its pre-click-time case; a
separate new-clock/old-sequence case remains. No production guard was weakened
and no prior experiment was replayed. This failure is retained as preparation
timing-fixture evidence, not a GUI outcome or a cross-platform timing claim.
After that fixture correction, Windows14 and pinned Linux unit03 14 tests
passed, exits0. No GUI/key injection/candidate/formal allocation occurred.
Remaining: independent recovery-phase checker and complete GUI callback/
candidate wiring, concrete new schedule, source/prospective freeze and first
actual GUI file-backed recovery run. Model-heldout acceptance remains unmet.

Independent stage-consistency increment: four new tests first failed with
ModuleNotFoundError for recovery_audit, then passed after implementing a
checker with no producer imports. Nine copied-record mutations cover absent
request, prior input, transferred sequence, pre-click ACK, wrong click target,
early emission, wrong payload, duplicate Save and boolean completion clock.
An effect-free STOP is accepted only as a stop, never a successful task.
Windows18 and pinned source-RO/network-none WSLc Linux18 tests passed exit0.
These are construction tests, not the first GUI allocation. Full independent
pipe-byte reconstruction and application-event/file binding are still required;
this stage checker alone cannot authenticate the caller's dictionaries.
The host swap-limit warning persisted. It does not invalidate these functional
checks, and it does not establish effective memory/swap caps or performance.

Real-Tk Save wiring construction: copied app.py/readiness_once.py/focus_trace.py/
focus_pipe.py from A11 without modifying A11. Initial test setup failed before
Save with missing FREEZE.json and an unwritable font cache; this was a new
construction harness, not a formal allocation. Added an explicitly non-formal
gui_construction/FREEZE.json fixture and private writable XDG cache. The next
real-Tk run reached Button.invoke and failed as intended: Save produced no
task_result.json. A12-derived app Save now calls save_once with target.get(),
stores its receipt before marking the save successful, and retains file errors
without showing success. Pinned Linux private Xvfb construction suite19 passed.
The Entry text was inserted programmatically (http://m_n), not emitted by XTest;
no focus-recovery hypothesis outcome or heldout/model claim follows from this.
The real file is checked against app Save by the independent file checker.
Next unfinished rung is candidate recovery wiring and complete pipe/effect
audit, not another replay of an earlier formal candidate. Local changes remain
outside repository until the complete frozen experiment package is prepared.

Phase/candidate wiring increment: a real OS-pipe recovery producer exposed an
auditor contract bug before any formal allocation: recovery_audit read a
nonexistent gate.checked_ns instead of gate.decided_ns. Its new regression
test first failed malformed_recovery:KeyError, then passed with the field
corrected; synthetic fixtures now match the actual producer contract.
Three phase tests first failed with missing run_phase. The new phase wiring
preserves observed-drift REFUSED as the prior outcome, invokes one explicit
RecoveryAttempt only in DRIFT_RECOVER, retains prior/total emission counts,
and leaves DRIFT_REFUSE effect-free and STABLE free of intervention/recovery.
Tests use real OS pipes with literal focus transitions, not GUI effects.
Windows23 discovered:22 passed/1 private-display test skipped. Linux23 passed.

Copied candidate.py/ready_guard.py/private_cache.py unchanged from A11 before
derivation. A new six-cell schedule test first rejected the inherited stale
control arm. A12-derived candidate now plans STABLE/DRIFT_REFUSE/DRIFT_RECOVER
over compact hmt (520x250+80+70) and offset hns (580x270+140+100), seed52612026.
It wires an explicit target recovery XTest click to the tested phase function
and passes each task's geometry/payload to the derived app. Pinned WSLc Linux
private-Xvfb suite24 passed exit0; this suite does NOT invoke candidate.run or
exercise that XTest click. Candidate wiring remains unproven until the first
frozen formal run. Source/prospective freeze and complete byte/effect auditor
remain unfinished. No formal run was started, consumed or replayed this turn.

Prior-phase independent audit increment: copied A11 drift/gate/sample/effect/
pipe/common/cache auditor helpers byte-for-byte, plus the A11 literal phase
test fixture as phase_fixture.py. New A12 prior_errors uses a deep-copy phase
projection, never mutates retained rows, and reuses independent drift polling
reconstruction. For DRIFT_RECOVER it checks refusal end <= recovery start,
zero prior counts, and every request/application KeyPress/Save >= recovery
start before excluding later effects from the prior no-input-refusal check.
Three tests first failed with missing prior_errors, then passed, including
four early-input/count/clock corruptions, missing drift poll, and unchanged
original record. Pinned private-Xvfb WSLc suite27 passed exit0. These fixtures
are construction-only; no new formal candidate was invoked. Whole-row pipe,
fresh recovery gate, final effects/files, source/process/visual custody and
top-level audit aggregation still need connection before source freeze.

Recovery-input join increment: three tests first failed with absent
recovery_input_errors. Added independent recovery-stage/click-geometry audit,
projected fresh gate reconstruction against retained frames/read boundaries,
and complete polling checks. New-clock/old-sequence, missing poll, wrong target
coordinate and unexplained total request count are rejected. Two full-input
tests then failed with missing input_errors. Added initial gate/poll, original
prior refusal, recovery gate/request and app effect joins, plus exact-int
emission count checks. Five corruptions remove each gate/drift join, break
app effect binding or substitute boolean counts. Added stable/no-recovery and
refusal/no-effect characterizations. Pinned private-Xvfb WSLc suite34 passed
exit0. No candidate.run or formal XTest recovery run was invoked. Top-level
packet/source/process/frame/file aggregation and synthetic packet qualification
remain before the first source/prospective freeze and formal allocation.

Whole-packet increment: four tests first failed with missing independent
inspect/expected_rows/verdict. Implemented source/image/schedule/process/ready/
focus/pipe/input/frame/cache/file aggregation. Synthetic six-cell packet
qualifies; ten copied-packet corruptions are STOP/UNQUALIFIED. A coherent
first-character misdelivery, application Save and independently saved wrong
file value remain METHOD_PASS/H_FAIL, not repaired or relabeled as STOP.
Required executed-source omission test failed for the absent coverage guard;
added explicit26-source coverage. Pinned WSLc suite42 passed. These records
contain synthetic bytes/source stubs and are not GUI outcomes.

Moved preparation byte copies to an additive package in the existing private
clone, new branch research/5260-file-recovery-a12-wslc-20261004 based on main
5796ff2b483d507b4b5275b2a6ef43e60f6092b5. Another corruption test first failed
because coherent but unplanned window dimensions were not rejected. Added
exact planned root-width/height check; synthetic builder now constructs both
planned sizes. Requested origin is a fixture command, not a guarantee that
Openbox decorations leave the actual root origin unchanged; actual geometry
and click coordinates remain independently retained and joined. No candidate
or formal allocation has run at this point. Original A11/preparation retained.

Final pre-freeze package checks: pinned private-Xvfb WSLc43/43 passed exit0;
Windows43 discovered42 passed/1 private-display test skipped. Eighteen common
A11 files byte-match and are listed in INHERITED.json; derived app/candidate/
new audit files have distinct new hashes. The dedicated package and commands
will be frozen prospectively before any candidate.run/XTest task allocation.
