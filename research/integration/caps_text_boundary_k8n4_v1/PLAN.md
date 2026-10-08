# #8254: public-dispatch Caps Lock operation boundary

## Scope and provenance

Date: 2026-10-07 JST. Intake main378ea2ec69aeedc0e4fbe3ce76d071fe023d4de5.
Source provenance: official Actions run37480784920/artifact11420528747 at
401d5171c91ed90097ac2de80c7df12a9f70e0b1. Download ZIP SHA256
8781069c7a5847eacd58fa73edcb544ed192244c41cd01e87025d3a04b633dbb.
The full artifact was integrity-checked, but this study freezes only the13 runtime
Python files actually imported by the public-dispatch construction, including2
packaging-generated blank initializers. All13 are retained, not AST excerpts.
Public API/core/backend/session blobs separately match intake main. The comparison
was truncated, so no complete-checkout equality is claimed. Research candidate
copies that closure and changes only text(); no shared runtime file is changed.
Prior #4003/#4038 and #8252 held-modifier work remain distinct. No blocked code used.

## H / T / D / C / U

H: lock-off at entry does not ensure lock-off after the program's own Caps_Lock.
A per-text LockMask check can refuse later text without changing the lock, replaying
input or discarding the completed prefix. It is NOT atomic with later characters.
T:2 arms x6 conditions x2 repetitions =24 fresh private GUI sessions. Four6-case
batches, CURRENT then TEXT_LOCK_GUARD in each repetition. Each case is one Python
public dispatch, one independent Tk Entry recipient, one private authenticated
TCP-disabled Xvfb. Two initial-state setup XTEST emissions only for starting lock on;
these are separate from task emissions and occur before application creation.
D: all24 complete; baseline wrong case4; candidate wrong case0, refusal6 (including
2 otherwise-correct digit-only requests); positive OFF/unlock/roundtrip exact in
both arms; prefix1 retained on candidate PROGRAM_ON; neutral held keys/buttons,
unchanged intended final lock, exact exits, raw audit and8 effective controls.
C: known cooperative default Xvfb/Tk, no other input client, authored source and
lease. Extra roundtrip and digit refusal are costs, not hidden benefits.
U: asynchronous change after query, intra-text ABA, XKB group/latch, other modifiers,
IME, malicious source, app/network stalls, model usefulness and portability unknown.

## Declared cells

| Condition | Initial lock | Requested operations after focus | CURRENT value | GUARD value/status |
|---|---|---|---|---|
| OFF | off | text aB2 | aB2 | aB2/completed |
| INITIAL_ON | on | text aB2 | Ab2 | empty/execution_failed |
| PROGRAM_ON | off | text1, Caps_Lock, text aB2 | 1Ab2 | 1/execution_failed |
| PROGRAM_OFF | on | Caps_Lock, text aB2 | aB2 | aB2/completed |
| PROGRAM_ROUNDTRIP | off | Caps_Lock twice, text aB2 | aB2 | aB2/completed |
| ON_DIGITS | on | text12 | 12 | empty/execution_failed |

Each program ends with release_all. Exception cleanup is the unchanged backend
path; do not claim the normal final operation ran after a failure. Preserve raw
failed_op_effect generic uncertainty even when fixture evidence shows no suffix.
Expected task key events: CURRENT54 per6, GUARD34 per6, total176. Setup24 events
are outside app/task accounting. Three experimental processes percase=72, plus
four outer batch processes; no model or host/shared GUI process.

## Variables and units

| Symbol/name | Meaning (日本語) | SI unit | Definition/domain | Type |
|---|---|---|---|---|
| mask | Xサーバー修飾状態 | 1 | query_pointer mask, nonnegative integer | scalar bitmask |
| LockMask | Lock状態ビット | 1 | Xlib constant2 on tested protocol | scalar bitmask |
| value | 要求された文字列 | not SI | supported bounded text string | string |
| index | 原始操作位置 | 1 | zero-based integer in program ops | scalar integer |
| ns | 同一ホスト単調時刻 | ns (1e-9 s) | monotonic_ns brackets, not calibrated HID time | scalar integer |
| cases | 独立仮想画面セッション数 | 1 | fixed24, construction excluded | scalar integer |

Dimensional check: mask operations compare dimensionless bitfields. Time ordering
uses only timestamps from this host; no wall-clock/monotonic subtraction or latency
claim. Release observed at a query is not an exact physical release timestamp.

## Conditional argument

The baseline constructs key chords from requested letter case and keyboard mapping,
without consulting LockMask. Under the tested layout a locked Caps_Lock changes the
case of those same physical keycodes. Consequently a program can pass entry checks,
execute its own lock toggle, and then produce different literal text.
In the candidate, every nonempty text() first validates its full text plan, reads
LockMask and raises before any key_chord if it is set. Thus when it observes the
lock on, no character of that text operation is emitted by that method. Earlier
operations remain real effects; the existing execute exception path attempts input
release and reports the prefix. An explicit earlier unlock permits later text.
This establishes only the observed refusal boundary: a writer changing the lock
after the check can invalidate case semantics. No universal prevention theorem.
Digits illustrate conservative availability loss. Rejecting them is not success.

## Construction and stops

Retain red01 auth STOP before task input; FamilyWild was not selected by installed
python-xlib (exact family/address matching). FamilyLocal/hostname repaired setup.
red02 baseline returns completed with1Ab2 (RED safety expectation false).
green01 erroneously still baseline because patch anchor omitted an existing comment
and outer shell continued; retain as PATCH_NOT_APPLIED, not green. Hard outer shell
gate and exact anchor precede green02, which returns prefix1/execution_failed.
All these are excluded construction. Initial Issue interpreter note3.11.8 is
superseded by measured3.13.5 ENVIRONMENT.json before the retained allocation.

## Freeze, stopping and review

Publish exact executable sources, complete baseline closure, candidate patch and
reconstruction, plan/environment/hash freeze and read back before formal case0.
One attempt percell and batch. Stop further batches on nonzero driver/outer exit or
incomplete evidence. Expected semantic refusals are normal complete case records.
Do not regenerate consumed science to improve a wrapper. Preserve first audit.
A separately coded auditor imports no runtime/driver. Eight copied-evidence controls
must first pass intact, then reject effective mutation, not crash. Same author is
not independent review. No main merge without applicable checks and nonauthor
review. Only additive research files; parent Issues/global ROADMAP remain open.
