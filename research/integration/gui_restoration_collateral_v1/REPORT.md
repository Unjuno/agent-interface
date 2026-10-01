# Live GUI restoration does not erase persistent collateral effects

Issue #4006; successor to closed #2076 / PR #2087, related #34 and #3936.

**Scientific result: PASS_LIVE_RESTORATION_COLLATERAL_SCOPED.** The deliberately
primary-only comparator fails in all six notification-enabled restoration cases.
This is neither a model evaluation nor production runtime promotion.

## Question and integration decision

Can the exact retained #2076 outcome reducer distinguish a restored GUI value
from a completely satisfied recovery contract when evidence is produced by real
native widget input instead of five hand-authored Boolean rows?

The tested contract is: restore the initial primary field and preserve the empty
notification journal. The protected collateral state is explicitly part of this
private application, not an assertion that stock Tk writes external messages.
A notification is a callback/Modified-handler append followed by flush and fsync.
The controller cannot delete, truncate, compensate, or directly invoke that sink.

**Handoff:** expose primary restoration and collateral preservation separately.
A completed compensating input operation is not proof of no earlier effect.
Unknown collateral evidence stays UNKNOWN. Neither a verified outcome nor a
notification receipt grants input authority.

## H / T / D / C / U

| Item | Frozen specification and disposition |
|---|---|
| H | Toggle-back and ordinary Text Undo restore the primary field without erasing earlier notification bytes; the unchanged reducer distinguishes partial restoration. Supported in this finite fixture. |
| T | 2 widget classes, 4 input/notification configurations, 3 fresh repetitions: 24 app sessions, then 4 reporting-only evidence views each: 96 views. One formal invocation. |
| D | Exact primary transitions and notification bytes; full outcomes match; all 72 missing/foreign/generation views UNKNOWN; all key/button checks neutral; all app/server exits present; 24-row raw audit and 10 rehashed corruption controls pass. |
| C | Notification effects are deliberately configured application behavior. No effect on disabled configurations is a real nontrivial positive, not proof of arbitrary application rollback. Cooperative, isolated, no concurrent edits or delayed sink. |
| U | No population rate, calibrated timing uncertainty, GUI generality, model utility, crash/power-loss durability, or speed/token claim. The method for acquiring these complete receipts from arbitrary apps remains open. |

Frozen intake main: `81a004527e5124e54fb1f4da5785fc0c5640ef50`.
Exact predecessor Git blob: `3ccf652575837c5ab961e78b8e9d56c703f4187e`.
`predecessor.py` is byte-identical; its `reduce_outcome` function is imported
unchanged. The new `policy.py` adapts exact primary equality, separately read
notification bytes, and session/widget/generation-bound evidence. Deliberately
withheld or mismatched views never change the original evidence.

## Implementation assumptions

Provided Linux x86_64 execution container; CPython 3.13.5; Tcl/Tk 8.6.16;
installed Python-Xlib; native XTEST to an allocation-owned authenticated Xvfb.
Docker CLI/image identity were unavailable: **not Docker/OrbStack replication**.
`ENVIRONMENT.json` binds 103 executable/library/Tk/Xlib source files. It is not
an attestation of every host component. CPU scheduling and frequency were not
controlled; there is no latency-performance gate. No install, provider/model,
network experiment, user desktop, clipboard, or shared-runtime operation.

Checkbutton uses unmodified TCheckbutton class bindings. Text uses unmodified
Text typing and `<Control-Key-z>` Undo. The fixture registers normal application
notification callbacks; the Text handler resets only its Modified notification
flag, never text content. IPC permits snapshots and close only. Native key/button
input, app input events, transitions, notification records, independent file
reads, raw IPC, process exits and X-server state queries are retained separately.

Official API context (consulted 2026-09-22):
- https://www.tcl-lang.org/man/tcl8.6/TkCmd/ttk_checkbutton.htm
- https://www.tcl-lang.org/man/tcl8.6/TkCmd/text.htm

These describe variable-backed checkbutton state and Text Undo/Modified behavior;
they do not predict or prove this application's collateral-effect result.

## Observed formal results

Each table row has three Checkbutton and three Text sessions.

| Sequence | Checkbutton primary | Text primary | Notifications per session | Full-evidence result |
|---|---|---|---:|---|
| NO_INPUT | 0 | empty | 0 | COMPLETE_SUCCESS |
| CHANGE_ONLY | 0 -> 1 | empty -> x | 1 | FAILURE |
| RESTORE_WITH_NOTIFICATIONS | 0 -> 1 -> 0 | empty -> x -> empty | 2 | PARTIAL_PRIMARY_RESTORED |
| RESTORE_WITHOUT_NOTIFICATIONS | 0 -> 1 -> 0 | empty -> x -> empty | 0 | COMPLETE_SUCCESS |

COMPLETE_SUCCESS is success under the stated recovery/no-change contract. It is
not completion of some unrelated desktop task. NO_INPUT is a trivial control;
the disabled-notification restoration supplies six nontrivial positives.

Full evidence produces 12 COMPLETE_SUCCESS, 6 FAILURE and 6 PARTIAL_PRIMARY_RESTORED.
All 24 views with withheld collateral, 24 with foreign session and 24 with wrong
generation produce UNKNOWN. Those are 72 derived reporting controls, not extra
GUI samples. The primary-only comparator reports complete in all 6 restored but
collaterally changed cases. Its negative result is retained, not hidden by the
scoped study PASS. The typed candidate has zero such false complete reports.

All 24 initial, final and cleanup server observations have empty key/button
states. All 24 app exits and the owned Xvfb exit are 0. Formal outer exit is 0,
stderr empty, timeout false. Formal invocations 1; retries/replacements/tuning 0.

### Why this is a counterexample, not a general theorem about Undo

Take any retained notification-enabled restoration row. Its initial primary
value and its final primary value are identical, both by value and type. Its
initial journal is empty. Its final journal contains the two actual notification
records; separate-reader bytes equal the bytes retained after app exit. Thus the
primary condition holds and the collateral condition does not. A policy that
calls this complete from the primary condition alone violates this declared
conjunction. The unchanged reducer instead reports PARTIAL_PRIMARY_RESTORED.

This witness establishes the insufficiency of primary-only evidence. It does
not show that every Undo leaks an effect, that notifications are intrinsically
irreversible, or that this fixture exhausts compensation semantics. The disabled
configuration explicitly demonstrates another valid outcome.

## Measurement fields and units

| Field | Meaning | SI unit / stored unit | Domain and definition | Type |
|---|---|---|---|---|
| primary value | GUI field being restored | Dimensionless/text | Checkbutton integer 0/1; Text empty or x in this allocation | Integer or string |
| notification count | App-owned persistent notifications | Dimensionless count | Exact number of retained JSONL records, 0/1/2 here | Nonnegative integer |
| generation | Recovery-contract identity | Dimensionless | Expected 1; deliberate wrong generation 2; Boolean is not an integer receipt | Integer |
| mono_ns, before_ns, after_ns, reader_ns | Same-container monotonic observations | Second / stored nanosecond | One monotonic domain; relative ordering only, no absolute epoch inference | Nonnegative integer |
| keys / buttons | Server physical-input state | Dimensionless | 32 keymap octets and pointer button mask; all endpoints zero | Integer vector / integer |
| outcome | Reporting disposition | Not applicable | COMPLETE_SUCCESS, PARTIAL_PRIMARY_RESTORED, FAILURE, UNKNOWN | Enum string |

Unit check: temporal checks compare nanoseconds with nanoseconds; application
strings/integers and record counts are not mixed with clocks. No ns-to-latency
benefit conversion or percentile estimate is used. Combined timing uncertainty
and coverage factor are not estimated because no timing claim is tested; that
is not an assertion of zero uncertainty. Repetitions are finite deterministic
fixture repetitions, not independent population sampling.

## Validation and retained limitations

Construction01: 8 sessions, one invocation, all exits0, 32 views, independent
raw audit zero errors. It is excluded from formal counts. No failed construction
or formal execution occurred. The intended primary-only policy failure remains
part of the result. Any later delivery incident belongs to this same Issue.

Frozen `audit.py` imports neither candidate, Tk nor Xlib. It reconstructs the
case schedule, native/app input agreement, typed primary transitions, notification
prefixes and post-exit bytes, IPC identities, outcome fields and neutrality.
Formal audit: 24 cases/96 views, errors=[], gate_failures=[]. Separate process
and implementation do not mean independent human review or separate trust roots.

Ten mutations reject after rehash: missing case, duplicate case, false complete,
altered notification value, Boolean generation, nonneutral key, missing process
exit, lost button release, UNKNOWN promoted, and altered snapshot. Four adapter
controls (Boolean generation, missing identity, string collateral flag, wrong
widget XID) all return UNKNOWN. This is a finite corruption set, not proof of
arbitrary auditor soundness. All eight frozen source/plan file hashes recheck.

## Revalidate without repeating GUI science

From this directory:

```sh
python unpack.py --out /tmp/gui-restoration-4006-readback
cd /tmp/gui-restoration-4006-readback
python audit.py formal01
python controls.py formal01
```

Unpack and raw-only audit use the Python standard library. `controls.py` imports
only the pure reporting adapter and predecessor, not the GUI runner. No new
allocation/model/GUI input is performed by these commands. Choose an absent
output directory. Do not rerun the consumed formal runner to reproduce the report.
`FORMAL_INVOCATION.json`, `FORMAL_EXIT.json`, the freeze and full raw files remain
in the lossless evidence archive. A fresh live replication requires a separately
frozen allocation; it does not overwrite this result.

## Roadmap and cross-domain handoff

Completed scientific stages: intake and collision check, source reconstruction,
excluded construction, public hash freeze, single formal run, raw audit and
corruption controls. Publication/main readback are separate delivery gates.
Only the additive `research/integration/gui_restoration_collateral_v1/` namespace
is owned. #34/#2197/#57 and the global roadmap remain open.

Human-computer interaction: distinguish a restored control value from the user's
full recovery intent. Transaction processing: compensating updates need not erase
already emitted notifications. Observability/event sourcing: current state and
history answer different questions, and missing history is not a zero count.
These are integration implications, not empirically validated cross-domain gains.
