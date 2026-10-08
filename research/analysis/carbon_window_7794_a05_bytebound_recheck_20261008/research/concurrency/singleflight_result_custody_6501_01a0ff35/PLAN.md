# Shared-result custody boundary, Issue6501

Worker01a0ff35-2ef3-7911-9911-f31862ad642f, FINAL-v5.
New allocation6501-RESULT-CUSTODY-NATIVE-20261003-01a0ff35-A01.
Intake main6da2b492b9c2a9d76e5c54d35a0ae50b7b49edde.
Unique branch research/6501-result-custody-01a0ff35-20261003;
package research/concurrency/singleflight_result_custody_6501_01a0ff35/.

H: equivalent requests and a completed shared Future do not by themselves
guarantee that an unaffected waiter's parsed-JSON snapshot remains the original
result. Caller editing and original owner-buffer reuse are distinct boundaries.
Completion-time deep snapshot plus private delivery, or canonical immutable
bytes at completion plus private parsing, should isolate both under this fixture.

T: actual native CPython3.11.9 asyncio tasks/Futures and explicit Event barriers;
two waiters register before producer release, A receives before a mutation,
B receives after it. Six policies and five schedules,30 rows/60 deliveries.
Policies: independent (two reads); shared; shallow_delivery; deep_delivery;
deep_completion (private deep copies at completion and each delivery);
json_completion (immutable canonical bytes at completion, fresh parse/delivery).
Schedules: none, caller_top, caller_nested, caller_list, owner_nested.
All sources start with the same inert parsed-JSON fixture. The original owner
mutation affects only the first read's retained object; independent B uses its
separate second read. It is not a changing external application truth.

Before comparison, freeze plan/input/candidate/raw-only auditor/runner and exact
installed runtime source/binary hashes. Exactly one comparative process and
one auditor process, caps1/1, retries0, raw<=1MiB, process timeout10s each.
Tiny construction cases are separate and precede the freeze. Any first failure
or stop is preserved; do not rerun this allocation or relax its gates.

D: PASS_RESULT_CUSTODY_CHARACTERIZATION_SCOPED only if every row, complete event
order, original snapshot, actual read count, returned value, observed identity
relation and terminal cleanup match the independently reconstructed contract;
all eight declared copied-raw corruptions must reject for their named reason.
Shared/shallow/deep-delivery counterexamples are deliberately retained, not
excluded or labelled safe. Both completion-isolating policies must preserve B
in all five schedules. Any unexplained difference is FAIL/HOLD.

The raw records a deliberately incomplete scope-only descriptive admission
control and a digest-integrity gate. A same-scope changed nested answer can fool
the incomplete control; recomputing the frozen snapshot digest must refuse it.
Neither control grants authority or dispatches an action. Snapshot isolation
does not replace per-waiter generation, deadline, cancellation or authority
checks. One shared read is not independent corroboration.

C: fresh private observations already avoid this alias; immutable result APIs
or existing per-waiter digest checks may already be sufficient. A shallow copy
isolates root edits but retains compound-object references. Copying only at B
delivery can copy an owner-modified source. This is standard object ownership,
not a novel concurrency algorithm or a discovered deployed runtime flaw.

U: plain authored JSON and deterministic barrier schedules only; no cycles,
custom Python objects, producer failure/cancellation/deadline race, real demand,
GUI/currentness/effect/physical release/authority or latency/resource benefit.
Counts are authored cases, not statistical samples. No model, network, backend,
WSLc/container/GPU/display/input/shared-resource lease or main write.
Shared fleet deadline unavailable and unextended. Historical T0/T0b and all
6501 cancellation/type/socket/executor/deadline allocations are untouched.

| Field | Meaning | SI unit | Domain/type |
|---|---|---|---|
| generation | Fixture source generation | 1 | integer7, no physical clock |
| read_calls | Actual producer coroutine entries | 1 | integer1 or2 |
| visible | Fixture predicate value | none | Boolean, originally false |
| sha256 | Canonical snapshot identity | none | lowercase64-character string |
| events | Actual barrier/transfer sequence | none | ordered record list |
| identity flags | Observed Python object sharing | none | exact Booleans |

Primary references: [copy semantics](https://docs.python.org/3.11/library/copy.html)
and [asyncio Futures](https://docs.python.org/3.11/library/asyncio-future.html).
The website currently describes3.11.17; this run is explicitly3.11.9 with exact
installed source/binary pins. No documentation code is copied. Standard-library
dependencies are Python Software Foundation licensed; our fixture/oracle are
independently written. Searches: all25 issue records plus bounded all-state
singleflight/mutable/snapshot/deepcopy queries; no exact experiment returned.
Search bounds do not establish global absence.

Preexecution publication correction (comparative candidate/auditor0/0):
The first own no-checkout worktree had an uninitialized index. Local source
commit451ba9ce4361839bb3e2800faf83c540658da00e accidentally omitted the base
tracked tree. That commit/ref/worktree and its original FREEZE remain private
and unchanged; no ref was pushed and no comparative process ran. A separate
full-base additive source tree preserves every original base entry, uses the
identical candidate/auditor/fixture/runner and reuses their exact four-method
construction logs. The old freeze is retained as preexecution metadata; the
new prospective freeze binds the corrected source commit before comparison.
