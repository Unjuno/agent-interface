# #8254 — public Caps Lock text-operation boundary

## First retained outcome

**PASS_PUBLIC_TEXT_LOCK_BOUNDARY_SCOPED**, not product or universal input safety.
Source freeze commit73f7ed0b3140e88432dbfb1ad9ec1890848f27c5 preceded all24 cases.
Full source treebe7f188f6f2775dfafd3e279c65fb2bab4c26204 matched local Git objects
and remote recursive readback before the allocation authorization comment6021898711.
First result was recorded in Issue comment6021934906 before packaging.

| Per12 fresh sessions | CURRENT | TEXT_LOCK_GUARD |
|---|---:|---:|
| Exact complete literal results |8|6|
| Wrong-case strings reported completed |4|0|
| Explicit text-operation stops |0|6|
| Task key events / native emissions |108|68|

Six conditions, two policies, two repetitions; independent new Xvfb/Tk each time.
24 public dispatches,72 experimental processes (24 driver/24 app/24 Xvfb),
four outer batch processes. All actual exits0. Xvfb was intentionally terminated
after terminal-state measurement; exit0 is not a claim it ended spontaneously.
Setup uses24 additional private-server XTEST emissions before app creation;
these are not app/task events. No model/user desktop/real host input.

The critical counterexample is one admitted program requesting text1, Caps_Lock,
then text aB2. CURRENT produced1Ab2 and completed; candidate produced prefix1 and
execution_failed in both repetitions. The per-text check does not silently undo
the explicit lock operation. INITIAL_ON gives Ab2 versus an empty stopped result.
Explicit unlocking and double toggle followed by text work in both policies.
Locked digits are correctly typed by CURRENT but refused by the candidate: two
lost otherwise-correct completions. Six candidate stops are not six task successes.

All24 terminal X-server keymaps and button masks are neutral; intended final lock
state persists. Actual release records are retained24/24. Generic failed_op_effect
remains unknown; may have emitted partial input. The fixture's exact prefix and
absence of later key events are independent evidence for these cases only.

## Audit and scope

First frozen raw-only audit:1316 checks/errors=[];8/8 effective copied-evidence
mutations rejected after every intact copy passed. Source/gate changes after
public freeze0; scientific reruns/replacements/exclusions0. Auditor is separately
implemented but by the same author, NOT genuine nonauthor review. No eligible
merge can be inferred from these checks alone.

H/T/D/C/U, proof and variable/unit table are in PLAN.md. Assumptions include the
known Xvfb keyboard layout, cooperative Tk, caller-authored state/lease and no
external writer during the operation. LockMask checking is not atomic with XTEST,
and does not solve #4038 intra-text ABA, XKB group/latch, arbitrary modifiers, IME,
unknown application semantics or physical HID timing. It adds a query and denies
some safe text. No latency/token/reliability/production-readiness claim.

## Construction retained, not relabelled

Four excluded attempts: red01 pre-input authentication STOP; red02 baseline wrong
string; green01 inadvertently unchanged baseline after a patch-anchor setup failure;
green02 patched prefix-only stop. FamilyLocal/hostname repaired authentication,
and hard setup failure plus the exact existing-comment anchor repaired construction.
The raw green01 arm label is historical, not evidence that candidate code ran.
All original first records and red01 source are retained. No old experiment copied
from blocked-publication lanes. Initial Issue interpreter note3.11.8 was corrected
before freeze to actual CPython3.13.5; immutable ENVIRONMENT.json is authoritative.
One GitHub update_ref call used an invalid argument name, then the schema-correct
fast-forward succeeded. This was not a tool safety block or a scientific retry.

## Reproduction and adoption decision

Run `python -B verify.py` here to reconstruct every277 exact raw/development/
outer/audit/provenance file in a new temporary directory, reconstruct the explicit
candidate source from the pinned baseline, and reproduce both saved audits exactly.
It starts no GUI/driver/batch and does not consume old allocations again. Private
Xauthority cookies were intentionally ephemeral and are never published. The
artifact provenance manifest lists unused modules too; only the13 actually imported
runtime files are in this source closure, with no complete-checkout claim.

All additions remain under the owned research directory. No shared runtime,
workflow, index or foreign branch changes. Candidate patch is a reviewable research
option, not a silently enabled production default. #4003/#4038/#57/#5085 and global
ROADMAP remain open/separate. Required next gate: exact-head nonauthor review and
applicable checks; production adoption needs an explicit decision about conservative
lock rejection and residual intra-operation races.
