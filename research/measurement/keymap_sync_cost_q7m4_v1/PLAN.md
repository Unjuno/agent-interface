# X11 observation synchronization cost: Issue #4357 / parent #2107

Prospective allocation q7m4-20260925-01. Source-first full public freeze required.
Only research/measurement/keymap_sync_cost_q7m4_v1 changes. No runtime adoption.
Previous focus/keymap experiment is already delivered by PR #4123 and is never rerun.
Local 1404-file prior ZIP was re-audited byte-exactly; PRIOR_CHECK.json records it.

## H / T / D / C / U

H1: avoiding XQueryKeymap while retaining XSync does not avoid a synchronous X11
request. SYNC_EVENT and QUERY_ONLY should each advance the observer request serial
by one; SYNC_PLUS_QUERY by two. API counts, X11 requests, socket packets, model
roundtrips and task latency are distinct quantities.
H2: event/query median paired native-wall ratio <=0.80. H3: query/double-sync
median paired ratio <=0.80. These timing hypotheses are separate from H1; a miss
is HOLD, not a reason to change gates or hide the negative result.

T: 3 arms x4 schedules x5 repetitions x32 measured samples =1920, 60 fresh
native worker processes on five fresh authenticated TCP-disabled private Xvfb
servers. Retain two excluded warmups per block (120 total). Each repetition is
one immutable 12-block batch. Order: schedule0..3; arm=(position+rep+schedule)%3.
No new model/provider, external network, user display/data, installation,
production runtime, application text effect or task success is involved.

The actor owns two mapped windows. Observer selects only the target and negotiates
detectable autorepeat. Oracle is a third connection in the same native process,
not an independent process/trust root. Each sample resets Shift UP off-target,
drains that baseline, focuses target, then obtains a normal FocusIn/Keymap basis.
Four schedules: no change; target Shift DOWN; focus away/DOWN/return; focus
away/DOWN/return/target UP. Actor sync and two oracle endpoint keymaps establish
quiescent source. Oracle bytes never enter the event reducer. Actual XTEST setup
input is not counted as task input. Only fixture Shift is operated; final full
keymap and pointer mask must be neutral before windows/server terminate.

SYNC_EVENT: XSync(False), local already-queued event drain/reduction.
QUERY_ONLY: XQueryKeymap, identical local drain/reduction, query-bit answer.
SYNC_PLUS_QUERY: XSync(False), XQueryKeymap, identical drain, query-bit answer.
The first is structurally motivated by the retained observer, NOT byte-identical
execution of the old Python/IPC/Tk pipeline. No additional polling thread,
stream-loss detector, input authority or production optimization is introduced.

Timing brackets contain the native acquisition calls, equal event reduction and
two CPU-clock reads. They exclude setup, initial baseline, oracle queries,
serialization, process/server startup and teardown. Raw CLOCK_MONOTONIC and
CLOCK_PROCESS_CPUTIME_ID endpoints, XNextRequest and XLastKnownRequestProcessed,
all bootstrap/measurement events and keymaps, native start/end, argv and actual
exits are retained. No subtracting X-server millisecond time from host nanoseconds.

D: all1920 measured/120 warmups/60 blocks/5 batches, source integrity, actual
process exits, final neutrality, exact exposure sequences and separate raw-only
audit must pass. All three answers and event reconstructions agree with both
oracle endpoints. Serial deltas1,1,2 and completed reply serial =next serial-1
are mandatory. >=8 effective semantic evidence mutations (planned12) must reject
AFTER an intact control passes. No fabricated measurements/exits or partial PASS.

Compute median duration in each32-sample block; then ratios across matched
(rep,schedule) blocks; then median over20 paired ratios. H2 PASS iff <=0.80,
otherwise HOLD_EVENT_LATENCY_BENEFIT_NOT_ESTABLISHED. H3 PASS iff <=0.80,
otherwise HOLD_REDUNDANT_SYNC_BENEFIT_NOT_ESTABLISHED. Report all ranges and raw
outliers without exclusions. Samples are serial/correlated, not1920 independent
host replications. No population confidence or calibrated physical error bar.

C: fixed native Xlib build, one watched Shift and quiescent cooperative source.
The benchmark includes a premeasurement oracle barrier; this is not asynchronous
arrival latency. A request/reply is not a measured TCP/network packet or universal
transport roundtrip. Persistent input grants, keyboard locks/latches/IME/grabs,
reconnection, unknown coverage, later writers and arbitrary app effects are out
of scope. A full keymap contains more information than the single reported bit.
Removing an actually required barrier solely for speed is not authorized.

U: supplied execution container, no Docker/OrbStack image identity. Exact actual
environment hashes/CPU affinity/clock descriptions in ENVIRONMENT.json; CPU
frequency, physical core isolation, virtualization and host load uncontrolled.
No calibrated combined uncertainty or coverage factor, no hard real-time bound,
model/token/task latency benefit or product claim. Separately coded raw auditor
is same-author, not independent human review.

## Variables, derivation and unit check

| Symbol | Meaning (Japanese) | SI unit | Definition/domain | Type |
|---|---|---|---|---|
| t0,t1 | 観測壁時計区間の始端・終端 | s | raw integer ns on same monotonic clock; t1>t0 | integer scalars |
| c0,c1 | 同区間のプロセスCPU時計 | s | raw integer ns; c1>=c0 | integer scalars |
| d | 観測処理時間 | s | (t1-t0)*10^-9 | real scalar |
| rb,ra | 次のX11要求シリアル番号 | 1 | before/after observation; no wrap in bounded run | integer scalars |
| N | 発行要求数 | 1 | ra-rb | integer scalar |
| m_E,m_Q,m_D | 各方式の32標本中央値 | s | event/query/double block medians | real scalars |
| R_E,R_D | 対応blockの時間比 | 1 | m_E/m_Q and m_Q/m_D | real scalars |
| code | Shiftキー番号 | 1 | 8..255 for one server | integer scalar |
| keymap | Xサーバーキー状態 | 1 |32 bytes/256 bits; not physical HID | bit vector |
| u_c,k | 合成標準不確かさ・包含係数 | s,1 | not estimated | unestimated scalars |

Subtract endpoints only within the same clock. Thus d has time units; dividing
block medians yields dimensionless ratios. Example: two durations20us and25us
have ratio0.80. This is a numerical illustration, not an observed benchmark.
Given a serialized fresh observer with no unrelated requests between rb and ra,
request serial increments count its issued requests by definition. Equality of
completed reply serial and ra-1 confirms processing through the last issued
request on that connection, not application effect or a later-world guarantee.
A positive initial keymap plus each complete ordered key transition determines
the watched bit inductively; a new FocusIn/Keymap forms a fresh basis. The raw
auditor reconstructs that basis and every subsequent transition. Losing any
premise yields UNKNOWN rather than extending this conditional claim.

ERROR CHECK: one native scope, two distinct timing ratios, no ratio-of-global-
medians substitution, no old formal rerun, no identity/authority from timing.

## Stopping / publication / roadmap

Construction01 used3 samples per block and is excluded. Compiler and construction
were successful; prefreeze review strengthens timeout retention and outer owned-
process-group cleanup, without changing science. Source/public freeze -> five
first-outcome batches (worker3s, outer25s) -> raw audit/12 controls -> complete
source/raw/report additive PR -> exact-head applicable CI/scoped review -> qualified
research-only main merge/readback. On timeout/source/cleanup ambiguity stop and
retain all partials under this Issue. No batch retry, replacement or post-result
gate tuning. No cleanup of foreign branches. Broad #2107/#2789/ROADMAP stay open.

Primary reference: X.Org Xlib C Language X Interface, handling the output buffer,
keyboard state and Key Map State Notification sections.
https://xorg.freedesktop.org/archive/current/doc/libX11/libX11/libX11.html
