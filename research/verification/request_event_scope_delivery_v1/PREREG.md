# Request event scope after exact-value verification

LOCAL preregistration; NOT yet a GitHub Issue. Frozen before formal measurements.
Origin: open #34 and #3048; #1873 explicitly distinguishes event lineage from
counterfactual causality. Prior chat-local exact-value result remains immutable.

## H
A current exact requested value plus a transport acceptance receipt does not
identify whether this accepted request committed a corresponding application
operation during its observation window. A typed, complete, application-owned
committed-event snapshot can distinguish no event, one event, duplicate events,
request-content conflict and unavailable evidence, without changing a final-value
verdict into a stronger execution claim. An operation that writes the same value
is allowed to commit; absence of a value change is not absence of execution.

## T
Allocation request-effect-scope-20260922-01. Twelve frozen scenarios, three fresh
private SQLite databases each: 36 cases, 72 separately exec'd application/observer
processes. Source and schedule are in plan.json. One synchronous formal invocation,
no retry/replacement/pooling/tuning; child timeout 3 seconds, supervisor 25 seconds.
Construction: 12 separate cases, excluded. Fourteen unit tests and fifteen
construction evidence mutations precede formal freeze.

Application commits its typed state and event in one BEGIN IMMEDIATE transaction,
SQLite DELETE journal, synchronous FULL. ROLLBACK control commits neither. No
crash cuts or concurrency after the final snapshot: those belong to parallel #3991.
The acceptance response marks only transport acceptance and records the current
committed event sequence. The observer starts after application exit and uses a
separate mode=ro connection with one read transaction for current state and all
events strictly after that acceptance floor. Raw process streams and database
bytes are independently checked. Candidate receives request/acceptance/delivered
snapshot only; no scenario ID or evaluator-only state. Previous exact-value
verifier is copied byte-for-byte, SHA256 651406db20f6dc55e33398d0c85fcda449b37633d3587370180b4d40682bc283.

Three comparisons on identical acquired state: unchanged exact-value verifier;
explicit naive promotion of that PASS to completion of this request; and new
state/event split. New consumer gets additional complete event evidence. This is
NOT an equal-information performance comparison. The naive promoter is new; no
allegation that production or the previous verifier made that promotion.

## D
PASS_REQUEST_EVENT_SCOPE_SCOPED requires all 36 rows and 72 exit-zero processes;
exact source/plan/request/transaction/byte/sequence/observer binding; original
value PASS count 33; new complete-this-request count 9; unsupported naive promotion
count 24; APPLIED_ONCE 12, NOT_APPLIED_IN_WINDOW 12, APPLIED_MULTIPLE 3,
REQUEST_CONFLICT 3, UNKNOWN 6; all individual frozen scenario gates; zero false
new completion under the independent oracle; independent audit and all 15
semantic evidence corruptions rejected. Completed contrary scientific behavior
is FAIL; source, timeout, incomplete denominator or ambiguous audit is STOP/HOLD.
No partial or construction outcome can rescue a missing formal denominator.

## C
State-only ENSURE/VERIFY goals may legitimately pass without executing a new
operation. OWN_NOOP and FOREIGN_THEN_OWN show an event can exist without being
necessary for the resulting value. APPLIED_ONCE means exactly one corresponding
committed event in this finite journal window, NOT globally exactly-once execution.
NOT_APPLIED_IN_WINDOW never authorizes retry and says nothing about future work.
The incomplete-history and wrong-incarnation controls are explicit delivery
perturbations of a retained valid observer record, not actual producer malice.

## U
Provided Linux x86_64 / CPython 3.13.5 / SQLite 3.46.1 container only. Docker/gh CLI
and pinned engine image unavailable; no Docker/OrbStack equivalence or attested
network-none. No model/provider, GUI/keyboard/mouse, user documents, installations
or experiment network calls. Same trusted fixture producer supplies event/state
truth; separate audit code/process is not an independent human review. Completeness,
identity, correct producer implementation and atomic participating effects are
assumptions. No authentication, arbitrary GUI causality, external-side-effect
atomicity, crash durability, future exactly-once, latency/token/product result.
Integer equality is the decision variable; monotonic nanoseconds only order local
process records. No physical uncertainty distribution, combined u_c or coverage
factor k is available or needed for this categorical scoped result.

## Field/variable table
| Field | Meaning | SI unit | Definition / range / assumption | Type |
|---|---|---|---|---|
| request_id | 要求識別子 | 1 | Opaque nonempty identifier; session scoped | string |
| session, resource, instance | セッション・対象・生成主体の寿命 | 1 | Trusted nonempty identities, exact match | strings |
| epoch | 要求の世代 | 1 | Nonnegative exact integer, boolean forbidden | integer scalar |
| floor, ceiling, seq | 受理時境界・観測終端・実行イベント順序 | 1 | Contiguous integer journal positions, closed final snapshot | integer scalars |
| saved, revision, payload | 保存状態・内容版・本文 | 1 | Exact bool/int/string tuple, not event cardinality | structured value |
| start_ns, end_ns, time_ns | 同一コンテナ内の時刻 | s (stored ns) | CLOCK_MONOTONIC; convert by one billion ns per s | integer scalars |
| complete_this_request | 当該要求の単発commitと要求値一致 | 1 | Boolean; never input authority or causal necessity | boolean |

Unit check: all snapshot comparisons concern dimensionless IDs/counts/typed values;
no wall-clock or physical-unit quantities are mixed with sequence numbers.

## Roadmap and ownership
Read current repository and preserve prior bytes -> excluded construction -> local
source/gate freeze -> one 36-case run -> raw database/process audit and mutations ->
additive patch/report/Issue+PR drafts -> publish via PR only when a write-capable
connection is actually available. Global roadmap, #34/#3048/#1873 remain open.
Do not touch parallel #3951 field-ablation, #3991 crash-scope, readers or X11 work.
No new separate research Issue should be manufactured for a local wrapper failure.
