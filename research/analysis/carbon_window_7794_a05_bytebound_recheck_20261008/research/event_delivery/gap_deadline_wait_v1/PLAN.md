# Gap notification wait scheduling — frozen local experiment

## Purpose and routing

Parents: closed #3986 (merged PR #4004), closed #926/#916; related #3876.
Question: Does restarting an 80 ms relative I/O wait after every irrelevant,
head-preserving event postpone a missing-predecessor notification, despite
using the unchanged elapsed-time notification predicate? Does preserving the
original absolute deadline avoid that postponement, and what remains when
a synchronous handler blocks the event loop?

This changes the scheduling/application boundary, not #3986's clock predicate,
its historical result or a publication wrapper. A substantive successor is
warranted for the wait-scheduling decision, but the current connection exposes
no GitHub write action, so this is a local prospectively frozen allocation and
an unposted successor draft. Do not pretend a GitHub reservation exists.
An execution/publication limitation is not a separate scientific Issue.

Concrete integration relevance: any future missing-event notification loop must
separate a gap's expiration from per-message inactivity, and must not infer a
hard service deadline from an elapsed predicate. This experiment is NOT a
production inbox, model interface, ACK system, safety-release controller or
adoption decision for #3876. No shared runtime/default will be edited.

## H — falsifiable hypotheses

H1: With the exact #3986 ELAPSED_80MS GapPolicy, a relative 80 ms selector wait
restarted after each tail E6 offer/duplicate can postpone notification of the
unchanged E4-missing/E5-head gap until approximately 80 ms after tail traffic
ceases. This is a new explicitly defined comparator, not a defect attributed to
the original GapPolicy or Python selectors.

H2: Recomputing the remaining wait from the original gap deadline and checking
due work before the next I/O wait prevents that per-message postponement in
the fixed finite traffic profiles. It must not notify before the original80 ms.

H3: Neither wait formulation can execute a notification callback inside its own
synchronously blocked150 ms handler. The fixed deadline only avoids adding
another80 ms after the handler returns. Deadline eligibility is not hard-real-time
service, host delivery, or model consumption.

## T — fixed local protocol

Actual environment is ENVIRONMENT.json: provided Linux x86_64 execution
container, CPython3.13.5, SQLite3.46.1, DefaultSelector=EpollSelector. Same
container CLOCK_MONOTONIC throughout. No Docker/OrbStack engine or pinned-image
attestation, no installs, external experiment network, model/provider, GUI,
keyboard/mouse, credentials or shared path. CPU frequency/load/affinity are not
experimentally controlled; observed affinity and guest CPU are recorded.

Source inheritance: copy gap_policy.py and contiguous_model.py verbatim from
our unchanged retained archive. GapPolicy Git blob
24221dedccca4914849c58e8edd61798ac7f9b14 is verified against current main
1f798cbb60b929e738c6bf8a5912470b38b45ff4. The old449-entry checksums and all72
old raw cases re-audit without rerunning their worker allocation. PR #4004 is
already merged, so do not republish or rerun it.

Two arms: RELATIVE_WAIT and DEADLINE_WAIT. Both use the same exact elapsed
gate and database model. Each fresh SQLite DB starts with only E3 retained in
the consumer, explicit ACK through E2, and E5 pending. There is no implicit ACK.
The separate orchestrator sends finite JSONL commands through an anonymous
pipe into one fresh exec'd worker per case. All scheduler waits, software-clock
brackets, incoming bytes, DB snapshots and actual child exits are retained.
The worker's event loop owns all model mutation, serialized in that process;
this is NOT a multiwriter race study. The auditor separately opens final SQLite
bytes and reconstructs every recorded state transition.

Five scenarios (times relative to the worker's first missing-gap sample):

| Scenario | Fixed command schedule |
|---|---|
| QUIET | No message before400 ms poll. |
| TAIL_TRAFFIC | Offer E6 at10,20,...,240 ms. Only first inserts; others are exact duplicates. E5 remains head. |
| BURST_THEN_QUIET | Offer/duplicate E6 at10,20,...,60 ms, then quiet. |
| PREDECESSOR_BEFORE_DUE | At30 ms offer E4 and use unchanged admission to drain E4 then E5. |
| BLOCKED_HANDLER | At30 ms enter an explicitly injected150 ms synchronous sleep; no other mid-block command. |

All scenarios then send a read/check poll at400 ms and stop at420 ms. Time
points are target offsets, not asserted realized timestamps. Both arms share
this nominal schedule and source, not identical realized scheduling. The wait
policy is the only treatment difference.

Formal denominator: five scenarios, two arms, three repetitions,30 fresh cases.
Arm order alternates by scenario/repetition, exactly as formal_schedule.json.
One formal orchestration; every worker timeout3 s, total supervisory timeout35 s.
The output path formal-01 must not exist. Preserve partials and stop on the
first source, process, unexpected exception or transport failure. No same-ID
rerun, replacement, pooling, extra samples or post-result tuning. No process
continues beyond this response. Construction01 is ten excluded cases, with nine
unit methods and12 semantic corruption controls; source review subsequently
strengthened auditor envelope integer/PID checks before the formal freeze.
The earlier construction audit stays unchanged alongside its V2 re-audit.

## D — decisions

PASS_WAIT_SCHEDULING_BOUNDARY_SCOPED requires all30 ordered cases, exact source
hashes, valid read-only independent audit, all12 mutation controls rejected,
actual orchestrator/worker exits0, all declared input bytes and neutral flags,
and the following scenario conditions in every repetition:

* Every persistent gap notifies once, never before80 ms. Each repeated receipt
  has the same content/identity. Notification never changes pending/consumer/ACK.
* QUIET: both first notices below200 ms.
* TAIL_TRAFFIC: actual successive worker tail-receive gaps stay below80 ms,
  final tail occurs at least230 ms after first gap; relative first notice is
  at least280 ms; fixed-deadline notice is below200 ms.
* BURST_THEN_QUIET: relative first notice is at least130 ms;
  fixed-deadline notice is below130 ms.
* PREDECESSOR_BEFORE_DUE: processing begins before80 ms, both arms drain E4/E5
  exactly once and produce zero gap notices afterward; ACK remains through E2.
* BLOCKED_HANDLER: handler straddles original80 ms; both first notices are after
  handler return. Fixed-deadline service occurs less than100 ms after return;
  relative service is at least80 ms after return.

A complete observed contract violation (early notification, state mutation,
incorrect receipt, wrong event admission) is a scientific FAIL. A missing or
corrupt source/process/row is HOLD_EVIDENCE_INTEGRITY; broken setup is STOP.
Failure to expose the directed timing discrimination under uncontrolled host
scheduling is HOLD_TIMING_EXPOSURE, not evidence of a universal timer defect.
The audit's conservative integrity status never silently upgrades a suspected
scientific violation. Diagnostic130/200/230/280 ms bounds distinguish this
one finite schedule and are not performance guarantees or production defaults.

Explicit final claims: observed relative-wait postponement, observed scoped
fixed-deadline service, and blocked-loop limitation. No general latency gain,
model usefulness, finished runtime or full roadmap completion is claimed.

## C — alternative explanations / constraints

Traffic carries actual E6 pending-offer/duplicate operations, not hidden polling
of the missing E4. A changed head could require a new deadline but never occurs
in these two traffic profiles. Predicate semantics, pending order, duplicate
binding, and inherited admission remain identical across arms.
CPU scheduling, pipe delivery, SQLite operations and raw-journal writes may
shift timestamps. Those costs are retained and symmetric in implementation,
not eliminated analytically. The blocking control is explicit injection, not a
measurement of ordinary serialization or SQLite latency. The final400 ms poll
is a declared fallback and is charged, not hidden retry.

One head, one lifetime, no restarts, lost reservations, generation reuse,
reclamation, clock jumps, suspend, multiple producers, SIGKILL, OS input or
power loss is tested. Model preparation and ACK are absent; this is a cooperative
notification fixture, not a security exploit or liveness proof under all loads.

## U — uncertainty

Raw nanosecond integers are software timestamps in one CLOCK_MONOTONIC domain.
1 ms epoll timeout quantization/rounding, execution scheduling, journal and DB
costs dominate observed overshoot. Report n=3 medians plus full min/max per arm;
do not infer population confidence intervals from directed repeats. No calibrated
combined standard uncertainty or coverage factor is available; u_c and k are
NOT ESTIMATED. Clock resolution is not total timing accuracy. Proofs below are
conditional on event-loop progress and never set scheduling uncertainty to zero.

## Bounded roadmap

DONE at intake: main/README/CURRENT_GOAL/ROADMAP/failure-routing read; recent open
and closed Issues/PRs;118 returned branch names over three pages; targeted gap /
relative-timeout searches; PR4004 merge readback; unchanged predecessor bytes.
Then: separate construction -> exact local source/plan/environment freeze ->
one30-case formal orchestration -> independent raw audit and mutation controls ->
lossless evidence/conditional proof/report -> additive local commit and patch ->
PR/main only through an available authorized write route, exact-head checks and
review -> own branch cleanup only after provenance/dependency proof.

The current MCP lists48 read actions, create discovery returns no action, the
installed-plugin search finds only the existing GitHub connector, local gh/docker
CLIs are absent and direct GitHub DNS fails. This is the current local execution
surface, not a claim about all workers or a permanent repository limitation.

## Variable table and conditional argument

| Symbol | Meaning (Japanese) | SI unit | Definition | Domain / assumptions | Type |
|---|---|---|---|---|---|
| t_0 | 同一欠落の最初の観測時刻 | s | first_ns converted from ns | one monotonic domain, nonnegative | scalar |
| B | 欠落通知の最短待ち時間 | s | 0.080 s in this study | positive, diagnostic only | scalar |
| d | 固定した通知適格期限 | s | t_0 + B | same gap lifetime | scalar |
| t | 待機直前の時刻 | s | clock_sample_ns converted from ns | t >= t_0 | scalar |
| w | selectorに渡す待ち時間 | s | policy-specific maximum wait | nonnegative, before notice | scalar |
| r_i | i番目の無関係な読取可能イベント時刻 | s | completed I/O readiness interruption | ordered finite arrivals | scalar sequence |
| i | イベント添字 | 1 (dimensionless) | index of arrival | positive integer | scalar integer |
| j | 最後のイベント添字 | 1 (dimensionless) | final index in a finite burst | positive integer | scalar integer |
| q | 同期ハンドラの実行再開時刻 | s | return of blocking handler | later than d in blocked case | scalar |
| L | 欠落観測から通知までの時間 | s | notice sample minus t_0 | nonnegative observed duration | scalar |

For the same unchanged gap, definition gives d=t_0+B. DEADLINE_WAIT recomputes
w=max(0,d-t), whereas RELATIVE_WAIT always chooses w=B after each processed
message. Unit check: both d-t and B are seconds, so their maximum and selector
argument are seconds. Code uses integer ns until conversion by1,000,000,000.

Assume ideal instantaneous handlers and selectable arrivals with each next
arrival strictly before the current relative wait expires. The first arrival
returns the first wait without timeout; the relative loop then starts another
full B. Apply the same argument to each subsequent arrival in order. By
induction no timeout callback executes during that arrival sequence. If the
finite sequence ends at r_j, the next relative expiration is r_j+B. If such
arrivals continue indefinitely and the loop always takes the readiness path,
there is no relative timeout callback. This is a conditional starvation result,
not a probability inferred from a finite trace.

For DEADLINE_WAIT, each prior arrival leaves d unchanged and only reduces d-t.
Once the loop samples t>=d, the computed w is zero and its explicit due branch
checks the unchanged gate before another select. Thus unrelated I/O does not
renew the gap's authorization to postpone notification. This conditional result
requires that the loop actually executes that branch. It does not bound CPU,
I/O, handler, or delivery delays.

If the same event-loop thread is synchronously blocked across d until q, neither
arm executes a check within that interval. The earliest possible fixed-deadline
service is at/after q; the relative implementation begins a new B wait after q.
This proves why elapsed eligibility and even an absolute timeout cannot alone
establish hard notification-delivery deadlines.

ERROR CHECK: the induction assumes unchanged gap identity and sub-B readiness
spacing; actual traces verify those exposure conditions. No implicit assumption
of zero scheduler delay is used in the empirical gates. All diagrams and timing
claims are notification-only and cannot authorize action or infer ACK.

## Primary sources checked at intake

Repository main1f798cbb60b929e738c6bf8a5912470b38b45ff4, Issue3986, PR4004,
docs/ISSUE_FAILURE_CLASSIFICATION.md; fetched via GitHub MCP.
Python official selectors documentation: select returns on registered readiness
or timeout; a timeout is supplied to each call.
https://docs.python.org/3.13/library/selectors.html
Python official time documentation: monotonic clock differences and scheduling
can exceed a requested sleep. https://docs.python.org/3.13/library/time.html
These establish API assumptions, not local outcome claims.
