# Same-event text validation: placement immediately before insertion

## Result and publication status

**PASS_DISPATCH_PLACEMENT_BOUNDARY_SCOPED**, one locally frozen allocation,
36 fresh Tk applications in two immutable18-case batches. No formal rerun,
replacement, excluded formal row, or source/gate change. A separately implemented
raw-only audit returns exit0,29913 checks,errors=[],12/12 corruption controls.
Fifteen pure unit tests pass before and after measurement.

**GitHub publication remains BLOCKED_GITHUB_WRITE_ACTION_UNAVAILABLE.** All48
exposed GitHub actions are reads; provider discovery returns the same installed
provider. No gh is installed. A bounded `git ls-remote` attempt additionally
failed to resolve github.com (exit128). This is a local access limitation, not
GitHub/repository-wide unavailability or a scientific failure. No remote Issue,
comment, branch, push, PR, merge or deletion occurred. The forthcoming local
patch/branch is NOT a main-derived GitHub branch. Global ROADMAP is incomplete.

## What changed from the prior research

The previous54-case text_resume_context study required no editing-state change
between its full-context check and the next key. It remains unchanged: supplied
422-file ZIP SHA25636eb18121821f4f1423dfece9ca14dad8ee17164f66733df47db70d43e6f8df8;
421 original manifest entries passed and the old raw-only audit reproduced
byte-for-byte. This continuation emits zero predecessor experiment input.

The new question is where the same editing-state predicate must execute if a
relevant change occurs after the sender's check. Current parallel #4040 owns
suffix recovery; #4036 owns target-activation recipes. Neither is modified or
rerun. #245's receiver-transaction plan is related known-mechanism context.
Closed #4043 and #4038 were inspected but not repeated. Initial main was
2308b8301d69b7089a2e0636486736ed59b61537; final read main was
33e86e997d02b769af17a3f03f6035c68927da6e. The actual upstream backend Git blob
remains9cae101a219348077668c8fc086acf8e13154afe. The new publication path returned
404 at the final pinned main. Searches/138 returned branch names are bounded,
non-atomic reconnaissance; unpublished parallel work remains unknown.

## One-factor experiment and exact results

All apps start blank. Native a,b insert prefix ab. After verified key release,
all policies perform the same valid full EDIT_CONTEXT check. Then one c key
press/release is emitted. The variation is whether/where the same predicate is
rechecked inside the actual app key-dispatch path. Ordinary stock Tk Entry
bindings, not RPC insertion or event_generate, cause text effects.

|Check placement|Cases|Correct bounded append|Refused Entry insertion|Incorrect edit|
|---|---:|---:|---:|---:|
|HOST_ONLY|12|4|0|8|
|EVENT_EARLY, before widget callback|12|4|4|4|
|PRE_CLASS, after widget callback and before Entry|12|4|8|0|

|Condition|HOST_ONLY A|EVENT_EARLY A|PRE_CLASS A|
|---|---|---|---|
|Unchanged state|abc|abc|abc|
|Caret moved to0 by RPC after host check|cab|ab, refused|ab, refused|
|ab selected by RPC after host check|c|ab, refused|ab, refused|
|Caret moved to0 by the c widget callback|cab|cab|ab, refused|
|ab selected by the c widget callback|c|c|ab, refused|
|Widget callback changes unrelated counter only|abc|abc|abc|

Each cell has two fresh app processes; all outcomes agree. The unrelated counter
changed once while B stayed blank. These repetitions are finite coverage, not
natural event frequencies or statistical reliability estimates.

The distinguishing actual order in EVENT_SELECTION is:

HOST_ONLY: host check passes -> native c received -> widget callback selects ab
-> ordinary Entry inserts c, replacing ab.

EVENT_EARLY: same host check -> native c -> app guard passes on ab/caret2/no
selection -> widget callback selects ab -> Entry replaces ab with c.

PRE_CLASS: same host check -> native c -> widget callback selects ab -> app guard
sees selection and returns YIELD_EDIT_CONTEXT/break -> no Entry insertion ->
ordinary release handling still occurs; ab and the selected range are retained.

Thus **inside the same event handler/event loop is not enough**. Relevant code
that runs after a guard can invalidate its premise without a thread race.
The last-placement result is conditional on there being no later relevant
mutation before the effect. It is not arbitrary atomic GUI control.

## Important distinctions

Every formal case emits the same6 native XTEST events,216 total:108 down/up
pairs for a,b,c. Receiver refusals block application insertion, NOT OS emission;
a native c is still delivered and released. There are36 native c events and
only24 suffix Entry insertions:12 incorrect,12 correct. The12 other c events
are deliberately refused (early4,pre-class8). All prefix insertions remain.

PRE_CLASS's8 refusals are unresolved partial states, not repaired or completed
tasks. Its4 successes are one-character bounded append results, not broad
application/task success. No model/provider call, token or end-to-end speed
measurement took place. Local evidence PASS is not runtime promotion.

## H / T / D / C / U

H: sender-side full-state validation can expire before a key is handled; an app
check before a changing widget callback can also expire within that one event;
after-callback/pre-Entry checking should block these two mechanisms.

T: three placements,six controlled conditions,two fresh repetitions; one excluded
18-case construction, then exactly two18-case formal batches. Source10 files,
plan/environment/intake locally frozen before any formal invocation. Actual
private authenticated Xvfb, separate Tk app processes, JSON-line barriers,
unchanged13-method X11Backend slice and unchanged inherited pure policy.

D: all36 raw cases/source identities/process exits/state transitions/command
counts/tag order and the exact table must agree. Independent raw-only audit
reconstructs editing state from journal events rather than scenario labels;
scenario names are only used for the separate frozen schedule/table test.
Every down has a received up, every sampled terminal X-server keymap/button mask
is neutral. All36 app,2 Xvfb,2 batch-child and2 outer-supervisor exits are0.

C: the fixture's widget callbacks are explicit controlled interventions. They
change only caret/selection/counter; never task text through RPC. The final
guard requires app cooperation and known binding order. `validate=none` and the
installed Entry KeyPress binding were read back. No custom validation,variable
trace,nested event loop,additional thread or later relevant handler is included.
X-window/focus/geometry stay fixed; the receiver uses the ticket's earlier native
metadata and does NOT freshly validate those OS fields. All3 placements have the
same additional fixture information, but this is not equal-support comparison
with an arbitrary uncooperative production application.

U: no guarantee for a later validation callback, Tcl update/wait/reentrancy,
unobserved widget changes, IME, keyboard grabs/locks, other applications,
concurrent input senders, authenticated event identity, later keys, rollback,
missing receipts, model behavior, efficiency, cross-platform or product claims.
The pending ticket is correlated only under a single cooperative input producer;
XTEST events do not intrinsically carry this experiment's ticket identity.

## Evidence and self-checks

The full tree retains all54 construction/formal app journals (events.json and
incremental journal.jsonl),effect snapshots,raw response/request strings,pixels,
commands,stdouts/stderrs/exits,plan,freeze,source,environment and old evidence.
Original source/snapshot archive is in predecessor/original_text_resume.zip.
Old result/status files are not edited or retrospectively called public.

Construction18 cases completed exit0 and were excluded. All construction audits
passed; the auditor was strengthened before formal freeze with per-batch source,
command and clock-envelope checks. Its two outputs remain. No failed formal
measurement was discarded. The container tool printed a terminal-clear/TERM
warning outside captured child/parent streams; both captured streams are empty
and actual exits are0. TOOL_OBSERVATIONS.md retains the observation without
attributing it to experimental code.

The frozen auditor imports neither GUI/backend nor candidate. It independently
simulates insertion/deletion from native character,caret and selection,checks
same-lifetime identities,ordered guard/mutation/class events,one-key ticket
binding,exact native counts,actual app effects and unchanged sources. It performs
29913 checks before the12 mutation-control challenges. Each altered-control test
first passes its intact counterpart. The separate implementation/process has the
same author; no independent human/agent approval or GitHub CI is claimed.

Freeze SHA256:15352b3db133778553e12a0b6c854678d2e059ad34216b3316af932710e0cf7e.
Audit SHA256:d6a99c101609ef089b01adf0a8369759b56f74e76b489bd45d7a5dba9554024a.
All10 frozen source files and all3 frozen documents remain byte-identical.

## Implementation assumptions, units and conditional proof

Tested Linux x86_64,CPython3.13.5,Tcl/Tk8.6.16,installed Python-Xlib,private
Xvfb480x240x24;420x170 app. Python/Xvfb/Tcl/Tk/native-library SHA256 values are
in ENVIRONMENT.json. No Docker/Podman/gh; no image equivalence. Source method ASTs
match the actual repository module, but public CLI/core admission/lease logic
is deliberately not included. X-server key state is not physical HID telemetry.

PLAN.md contains the variable table and complete conditional argument. All age
subtractions use same-container monotonic ns against the inherited1s budget.
X11 event timestamps are ms and are not mixed with that clock; character indices
are not display pixels. No performance comparison is claimed. Combined calibrated
uncertainty u_c and coverage factor k are not estimated for diagnostic times.

Primary references,read2026-09-22 (online8.6.18,actual test8.6.16):
https://www.tcl-lang.org/man/tcl8.6/TkCmd/bindtags.htm
https://www.tcl-lang.org/man/tcl8.6/TkCmd/bind.htm
https://www.tcl-lang.org/man/tcl8.6/TkCmd/entry.htm
The manuals describe binding order,break behavior and editing state. This is a
known-mechanism integration experiment, not a novel Tk theorem or defect report.

## Integration decision and roadmap

A cooperative application can expose an EDIT-specific conditional insertion
boundary, but its guarantee must name the final relevant mutation point and
exclude/revalidate reentrant or later callbacks. A preflight or early-event PASS
cannot by itself grant later editing correctness. Without application cooperation,
the universal OS-input route still has a residual interval and needs explicit
limits/postcondition handling; this experiment does not implement that fallback.

Human-computer interaction: edit-state-sensitive text handling. Runtime
verification: predicate-to-effect ordering. Workflow recovery: preserve partial
state and refuse without replay. Transfer to these fields is proposed,not measured.

Completed: current intake/parallel boundary,prior re-audit,excluded construction,
local freeze,two formal batches,independent raw audit/12 controls/15 units,full
local artifacts. Pending: supported GitHub write route,retrospective source/raw
Issue/PR publication,exact-main application/CI/review,merge/main readback and any
branch cleanup. The local branch must be retained while unpublished. No unrelated
branch is deleted; no pending remote merge is invented. Global roadmap is open.

## Read-only revalidation

After extracting into a fresh directory containing this report:

```sh
python -B verify_retention.py
python -B source/audit.py --root . --mode formal --controls
python -B source/test_gate.py
```

Never rerun consumed construction/formal IDs. Revalidation executes no GUI,input
or model call. The archive/patch include actual observed exits,not inferred ones.

## Postformal packaging correction

The first retention helper excluded every file named MANIFEST.json rather than
only its own root manifest. An explicit copied-tree mutation of the nested
predecessor manifest incorrectly passed. Its old helper/manifest and observed
FAIL_PACKAGING_NESTED_MANIFEST_COVERAGE are retained under packaging-first.
The postformal helper now excludes only the root manifest. The first displayed
member count396 was also corrected: the initial ZIP actually had397 members.
No formal source,raw result or scientific auditor changed. Final delivery counts
come from the archive central directory,not a derived guess.
