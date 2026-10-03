# #5372 queue-telemetry boundary — prospective finite experiment

Policy FINAL-v5. Worker `/root`, API workspace host `40c19c32e781`.
Parent: https://github.com/Unjuno/agent-interface/issues/5372 .
Run ID: `5372-TELEMETRY-CAP-20261003-API-A01`.
Branch: `research/5372-telemetry-cap-boundary-20261003-api`.

## Goal and decision

Determine whether a telemetry-based admission layer is necessary to bound
normal verifier work when queue reports are delayed or wrong, versus a simple
authoritative pending-work cap. This advances the parent's explicitly untested
misreported-telemetry residual, not the completed endogenous-demand T1,
route-expansion A01, or invalid/unaudited priority-fairness A02. Their sources,
raw and dispositions are unchanged. No new controller will be promoted merely
because a more elaborate policy can pass a synthetic case.

H: report-only admission can exceed a pending-work cap under underreporting;
adding an authoritative cap prevents that, but cap-only is sufficient and yields
at least as many completed synthetic jobs in every fixed case as report+cap.

T: one finite enumeration of all 243 five-tick arrival streams over 0/1/2
offers, crossed with three report modes, three delays, three service schedules:
6,561 paired cases, four policies, 26,244 arm traces. Each trace has eight ticks.
Each offered identity is either admitted once or explicitly UNKNOWN immediately.
FIFO service completes one admitted job on an enabled tick after admissions.
Service is UNIT, ALTERNATE (even ticks) or STALL (disabled ticks 0..2).
Ticks 5..7 always service one normal job to drain bounded queues.
Reports sample pending occupancy before admissions and service; delay 0/1/2
uses history at max(0,current tick-delay). ZERO is persistent underreporting;
HIGH is persistent report 2. These modes are deliberately fixed faulty signals,
not probabilistic error models. The measured report is incremented locally per
admission during a batch, even in the report-only control.

Four policies: REPORT_ONLY admits while report+batch admissions <2;
REPORT_CAP also checks actual pending count <2; CAP_ONLY checks only actual
pending <2; RATE_CAP also limits admission to one per tick. The cap counts
queued jobs, and each synthetic job has one unit of work, no in-flight separate
server occupancy. Admission/check/enqueue is atomic by the single-thread model.
There are no retries and no deadline-expired synthetic jobs.

Mandatory safety: one labelled safety event per tick, independently serviced
in that tick on a dedicated lane in every arm. This checks preservation/accounting
of an explicitly reserved lane only, not real input release, a scheduler deadline,
capacity contention, or safety under common-cause lane failure. Every normal
completion is the fixture's identity-bound unit-job oracle, not application effect.

D (fixed before corpus execution): `SUBSUMED_BY_AUTHORITATIVE_CAP_SCOPED` iff
(a) report-only has at least one cap violation, (b) all cap-based arms have no
cap violations or undrained jobs, (c) cap-only never completes fewer jobs than
report+cap or rate+cap and strictly exceeds report+cap in at least one paired
case, (d) independent reference reconstruction matches every exact trace and
all six effective corruptions are rejected, with complete case/offer/safety
accounting. Otherwise `FAIL_DECLARED_FINITE_HYPOTHESIS`; incomplete source,
audit or invocation evidence yields HOLD/STOP, never a synthetic PASS.

C: an actual central pending cap may already subsume the entire proposed
telemetry layer. A fixed-rate cap may be simpler but lose burst throughput.
If local pending count is itself delayed, remotely owned, or non-atomic, this
baseline's assumption fails and a distributed reservation design needs its own
evidence. Deliberate extreme report faults manufacture a boundary counterexample,
not prevalence, optimality, or typical usefulness.

U: complete only for the frozen finite model. No real queue, GUI, model, hardware
input, lease, freshness deadline, heterogeneous service cost, fairness guarantee,
token savings, live latency, stationarity or asymptotic stability is evaluated.
Exact synthetic completion does not establish useful feedback or task correctness.
Logical ticks have no mapping to wall time. Delayed honest reports may still be
useful in multi-stage systems excluded here. No OS/runtime change is proposed.

## Freeze, execution and audit

Construction checks use only hand-derived one/two-tick fixtures; they do not run
the formal five-tick corpus. Sources and this plan are SHA-256 frozen in FREEZE.json
before one candidate invocation and one separate auditor invocation. No retry of
this ID and no adjustment of decision thresholds after observing outputs.
The auditor imports no candidate code, uses a separate list-based reference,
reconstructs all traces and ordering, and rejects six value-changing mutations:
missing offer, forged verified count, hidden peak, lost safety event, wrong report,
and cross-task completion. This is implementation diversity within one author's
work, not nonauthor review or a claim of fully independent scientific assumptions.

Host execution is deliberately selected for exact finite enumeration per
docs/RESEARCH_METHOD.md. This analytical construction has no empirical OS
residual and does not consume any WSLc/Docker/live/model allocation. Python
stdlib only, one process per stage, requested RLIMIT_AS=512 MiB,
RLIMIT_CPU=60 s; raw output ceiling 64 MiB. Launcher records actual UTC, argv,
exit, stdout/stderr, host/runtime and byte hashes; output is exclusive-create.
No hidden background supervisor or restart is configured. No shared resource
is acquired. The 48h fleet start/deadline is unavailable; this bounded segment
neither sets nor extends it.

Delivery: additive evidence-only PR, with applicable construction checks,
raw readback and diff check. Main merge requires existing distinct nonauthor
agreement under FINAL-v5; neither author audit nor synthetic PASS is a vote.

## Symbols / units / types

| Symbol or field | Japanese meaning | SI unit | Definition / range / premise | Type |
|---|---|---|---|---|
| tick | 合成イベントの順番 | 1 (not physical seconds) | integer 0..7; no wall-time calibration | integer scalar |
| arrivals | 各tickの新規要求件数 | 1 | five integers, each 0..2; identical across arms | integer vector |
| delay | キュー報告の遅れ | 1 (logical ticks) | integer 0..2 | integer scalar |
| cap | 実際の未処理件数の上限 | 1 | exactly 2 unit jobs; admission is atomic | integer scalar |
| report | 制御側へ届く未処理件数 | 1 | historical pending, zero, or cap | integer scalar |
| occupancy / peak | service前の実件数 / その最大値 | 1 | normal queued unit jobs only | integer scalar |
| verified | 独立参照と一致する合成処理完了件数 | 1 | not GUI/application success | integer scalar |
| UNKNOWN | 受入れを拒否した要求の明示状態 | nonphysical label | no action/effect authorized | string enum |

One authoritative-cap admission requires current count <2 and adds exactly one
job, giving post-admission count <=2. Service removes zero or one job; induction
from empty queue proves the cap under the atomicity assumption. Eight ticks
are finite; stability for infinite arrivals is not inferred. Exhaustive execution
tests whether the candidate and separate reference implement that model and
quantifies offered-work dispositions/throughput cost of redundant telemetry.
