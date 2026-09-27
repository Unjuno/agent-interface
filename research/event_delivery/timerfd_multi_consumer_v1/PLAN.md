# Timer ownership at a two-process notification boundary

Allocation: `timerfd-multi-consumer-20260922-01`.
Prospective local plan; **not a GitHub preregistration**. No formal invocation
has occurred when this document is frozen. New additive path only:
`research/event_delivery/timerfd_multi_consumer_v1/`.
Proposed publication branch: `research/timerfd-multi-consumer-4001-20260922`.

## Lineage and concrete decision

Originating question #4001 reports single-owner timer-expiration accounting and
explicitly excludes multiple readers and descriptor duplication. Its first
formal result is already retained; no original experiment is rerun. Closed
#3986/#4031 concern elapsed eligibility and selector wait scheduling. The previous
conversation's `timer_episode_binding_v1` concerns application episode identity;
its archive remains unchanged. #3984/#3995 concern positions in regular files,
not the consumptive timerfd count or rearm/disarm state studied here.

The integration decision is whether handing a timer descriptor to two local
workers supplies independent deadline ownership or broadcast notification. Test
that assumption before composing notification/timeout workers. This is known
Linux-interface semantics validated in actual processes, not a novel OS theorem,
a security exploit, or an allegation that a production route duplicates timers.
No sensor, generic queue, background service or shared runtime is introduced.

## H — falsifiable hypotheses

H1: If A and B inherit aliases of one timer object, both can observe readability,
but after A consumes a one-shot expiration B gets EAGAIN. Reversing the read
order reverses the consumer. Readiness does not reserve one count per observer.

H2: Rearming or disarming A's alias after expiration clears the shared unread
expiration for B; B is not an independent timer owner. Separately created timers
preserve B's already-expired count under the same A-only operations.

H3: Closing just A's alias leaves B's timer/count available in both constructions.
Descriptor close is not timer cancellation while another live alias exists.

## T — fixed finite experiment and stopping

Two modes: SHARED_DUP (one timerfd_create and one dup) and INDEPENDENT_CREATE
(two timerfd_create calls). Both are CLOCK_MONOTONIC, nonblocking, one-shot.
Two fresh exec'd Python actors get only their one intended inherited timer FD
plus ordinary protocol pipes. Each duplicates its inherited FD and closes that
incoming FD. The orchestrator closes all its timer handles after actor readiness.
Thus no orchestrator timer handle explains the close control.

Five schedules: A_READ_FIRST, B_READ_FIRST, A_REARM, A_DISARM, A_CLOSE. For every
schedule both actors first report actual select readability before any test
read/mutation. Source-arm deadline is a common future monotonic timestamp,
100 ms after controller sampling. Rearm is 3 seconds ahead, never waited to
completion: the B read must occur before that deadline or the exposure is HOLD.
These intervals are fixture construction bounds, not performance thresholds.

Two repetitions of all ten mode/schedule cells: 20 fresh cases, 40 actors. Two
predeclared immutable ten-case batches, one repetition each. The second batch
reverses mode order within each schedule. Formal source/schedule freeze before
batch 0; batch 1 requires the real zero returncode receipt for batch 0. No
retries, replacements, exclusions, source/gate tuning or construction pooling.

Actor request timeout 2 seconds, select wait at most 1 second, process wait
2 seconds; outer foreground wrapper limit 25 seconds per batch. Unexpected
source/transport/process/timeout errors stop the allocation and retain partials.
The wrapper kills only its own created process group on timeout; absent actor
exit evidence remains missing, never inferred. Every process finishes within
this conversation; no asynchronous future work.

Construction: one excluded ten-case matrix plus six offline test methods and
12 semantic corruption controls. The first actual kernel probe created an
unarmed timer, read its fdinfo and closed it. Corrections may be made and retained
before the source freeze; formal data may not be rerun to repair a wrapper.

## D — exact decision gates

`PASS_TIMERFD_OWNERSHIP_BOUNDARY_SCOPED` requires all 20 registered cases, 40
actual actor exits, both real runner returncodes, the unchanged source inventory,
raw protocol completeness, independent kernel fdinfo snapshots and all outcomes:

| Schedule | SHARED_DUP | INDEPENDENT_CREATE |
|---|---|---|
| A_READ_FIRST | both initially ready; A=1; B poll=false/read=EAGAIN | both initially ready; A=1; B poll=true/read=1 |
| B_READ_FIRST | both initially ready; B=1; A poll=false/read=EAGAIN | both initially ready; B=1; A poll=true/read=1 |
| A_REARM | B loses old unread count; B has future remaining time | B keeps old unread count; B has no future remaining time |
| A_DISARM | B loses old unread count | B keeps old unread count |
| A_CLOSE | B keeps old unread count | B keeps old unread count |

All successful reads must be exactly eight bytes decoding to integer 1 in native
byte order; EAGAIN returns no data/count. Closed descriptors must produce EBADF
in the actor and be absent from the externally read fdinfo location. Endpoints
must remain authority=false and input_dispatched=false.

A complete interpretable mismatch is FAIL at the specified gate. Incomplete
process/clock/source/byte evidence is STOP/HOLD. A result supporting these
hypotheses does not qualify shared aliases as independent notification endpoints.
Separate timers also do not constitute two independent application observations.

The raw-only auditor does not import the worker or runner. It checks source
commitments separately, exact request/response frames, sequences, timestamp
brackets, counts, externally collected fdinfo tick/remaining-time values, explicit
FD creation topology and observed exits. Inode equality is deliberately NOT used
to identify timer objects: anonymous-inode metadata is not such an identity proof.
12 copied-evidence mutations must reject after redundant protocol frames are
reserialized; no reliance solely on a stale summary digest.

## Variable table / units

| Symbol/field | Meaning (日本語) | SI unit | Definition | Domain / premise | Type |
|---|---|---|---|---|---|
| A, B | 二つの読み手 | 1 | distinct freshly exec'd actor identities | exactly two per case | identifiers |
| f_A, f_B | プロセスごとのタイマーFD | 1 | handles passed and then duplicated by each actor | valid nonnegative descriptor until closed | integer scalars |
| Q_A, Q_B | 未読の満了カウンタ | 1 | kernel `ticks` before/after an operation | 0 or 1 for these one-shot exposures | integer scalars |
| d | 初回満了期限 | s | `initial_deadline_ns`, stored as integer nanoseconds | common CLOCK_MONOTONIC domain; future at arm | integer timestamp |
| d_new | 再設定した期限 | s | `rearm_deadline_ns`, stored as integer nanoseconds | rearm case only; B sampled before it | integer timestamp |
| t_before, t_after | システム呼出しを挟む時刻 | s | response start/end_ns | nonnegative, ordered, same clock domain | integer timestamps |
| R_A, R_B | 読取り可能性の観測 | 1 | select result per actor | Boolean, not a consumed receipt | Boolean scalars |
| C_A, C_B | 実際に読めた満了数 | 1 | uint64 from exactly eight returned bytes | 1 here; unavailable for EAGAIN | integer or null |
| N | 正式ケース数 | 1 | exact case denominator | 20, split into 10 + 10 | integer scalar |

Dimension check: a clock timestamp minus a clock timestamp is a time interval;
all stored values use integer nanoseconds on CLOCK_MONOTONIC. 100 ms is
100,000,000 ns and 3 s is 3,000,000,000 ns. Counts, FD identities and Boolean
readiness are dimensionless and must never be added to durations or labelled
as acquisition counts.

## Conditional argument (analytical reduction before measurement)

Assumptions: timerfd_create creates a new timer object; dup/inheritance produces
an alias of that object; successful read returns and clears its unread count;
settime replaces its schedule and clears its old unread count; the final close
frees the timer. Exactly one initial one-shot expiration occurs and there are no
unrecorded readers, mutators or tick-injection calls.

For shared aliases there is one unread counter, so Q_A and Q_B name the same
state. Before either reads it is 1. Observing select readiness has no consume
operation, so two true readiness observations leave that one counter at 1. The
first read returns 1 and sets it to 0. No second expiration can occur for the
one-shot timer; the second nonblocking read must therefore be EAGAIN. Swapping
actor names gives the reverse-order result, excluding a privileged-A rule.

For separately created timers the states differ. Consuming A changes only
Q_A. Q_B stays 1 and B returns 1. Each count comes from its own timer object,
not from broadcast delivery of one original expiration.

Rearm and disarm act on the timer object named by the descriptor. For shared
aliases, resetting A removes the same unread count B would read. For independent
objects B's state is unchanged. A future rearm also makes B's remaining-time
field positive only for the shared object. The explicit before-new-deadline gate
prevents a fresh expiration from being mistaken for preserved old information.

Closing A removes one reference, not B's reference. B still names a live object,
so its pending count can be read. Thus closing a worker's handle is not evidence
that another worker's timer is cancelled. These conclusions follow under the
listed API assumptions. The experiment checks actual Python/kernel/descriptor
wiring and external raw snapshots, not the mathematical truth of an unspecified
scheduler or production integration.

## C / U — scope and uncertainty

Trusted bounded local processes; no adversarial endpoint or third-party system.
No GUI, keyboard, mouse, model/provider, user document, experiment network,
installation, cancellation of unrelated processes, or shared runtime mutation.
Actual environment: provided Linux x86_64 execution container; no Docker/OrbStack
engine/image attestation. CPython and guest/kernel/CPU details in ENVIRONMENT.json.
The ABI is the Python 3.13 os timerfd wrapper and native-endian 8-byte uint64.

Scheduler delay and non-simultaneous software snapshots are relevant limits;
no timing efficiency, hard deadline, natural race frequency or reliability
probability is estimated. Snapshot predicates are stable between the declared
operations for one-shot timers; the future-rearm gate is independently checked.
No calibrated combined uncertainty u_c or coverage factor k is available or
appropriate for these exact count/order gates. CPU frequency/load are unpinned.

A broadcast design would need one owner plus explicit identity-bound delivery;
that mechanism is neither implemented nor measured here. Independent timers are
not an automatic recommendation for semantically one event. Production adoption,
useful model-facing feedback, recovery, physical release and the global roadmap
remain separate acceptance tasks. Separate audit implementation is by the same
author, not independent human review.

## Roadmap and publication

Intake/ownership -> excluded construction -> local immutable source freeze -> two
finite formal batches -> raw-only audit/corruption checks -> additive evidence
bundle and patch -> PR/check/review/main readback when an authorized write route
is available. No new Issue is created solely for a local publication limitation.
A successor to #4001 is justified by the changed multi-owner contract, not by a
new timeout or wrapper. The draft explicitly discloses local preregistration.

Primary references (API semantics, not evidence for this local run):
- https://man7.org/linux/man-pages/man2/timerfd_create.2.html
- https://docs.python.org/3.13/library/os.html#timer-file-descriptors
- https://github.com/Unjuno/agent-interface/issues/4001
