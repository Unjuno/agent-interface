# Timer expirations are not observation acquisitions

Issue #4001. Allocation `timerfd-observation-accounting-20260922-01`.

**PASS_TIMERFD_OBSERVATION_ACCOUNTING_SCOPED**, 21 first-outcome cases, no rerun.
The deliberately naive shadow counter separately **FAILS_OBSERVATION_OVERCOUNT**
in all six periodic delayed-reader cases. Nothing is promoted into runtime.

## Result

| Mode | Cases | Reported expirations per case | Mock callback receipts per case | Unobserved from reported expirations per case |
|---|---:|---:|---:|---:|
| PERIODIC_20MS | 3 | 21 / 21 / 21 | 2 / 2 / 2 | 19 / 19 / 19 |
| PERIODIC_60MS | 3 | 41 / 41 / 41 | 2 / 2 / 2 | 39 / 39 / 39 |
| ONESHOT_20MS | 3 | 1 / 1 / 1 | 1 / 1 / 1 | 0 / 0 / 0 |
| ONESHOT_60MS | 3 | 1 / 1 / 1 | 1 / 1 / 1 | 0 / 0 / 0 |
| DISARMED | 3 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| SHORT_READ | 3 | 1 / 1 / 1 | 1 / 1 / 1 | 0 / 0 / 0 |
| REARM | 3 | 1 / 1 / 1 | 1 / 1 / 1 | 0 / 0 / 0 |

All 21 actual worker exits and the external supervisor exit were zero. The
frozen raw-only auditor returned zero with no errors. All 12 semantic/provenance
mutations of formal data were rejected; the modified stdout digest was updated
before those semantic checks, so they did not rely only on hash mismatch.
Five construction unit methods passed before freeze. Construction timer probes
were unarmed/disarmed and are excluded; synthetic clock traces are not kernel
measurements. All timer descriptors closed with an independently attempted
fstat yielding EBADF. There were zero GUI observations, model calls, or inputs.

The 198 reported expirations produced exactly 24 **trivial mock callbacks**,
leaving 174 explicitly unobserved slots within the reported counts. These are
not 24 image/application observations. Three unread old-generation one-shots
were discarded at rearm and are outside that total. A reset does not recover
unread history or transfer it to the new schedule.

Raw JSONL SHA256: `1ab023c61cc7c4042ae6453d8ab95ae852f71097f84d609cbea981d27e9a145e`.
Frozen source manifest SHA256:
`c64a831de11f66494a0dff6713655ce93776e66192d0572e49ecce11926fc6a9`.
Preformal registration:
https://github.com/Unjuno/agent-interface/issues/4001#issuecomment-5766700954 .
First result:
https://github.com/Unjuno/agent-interface/issues/4001#issuecomment-5766718350 .

## H / T / D / C / U

**H.** A delayed Linux timerfd reader receives expirations, not independently
acquired historical observations. A single-owner adapter can account separately
for raw reported expirations, actual callback invocations, and unobserved slots.
Rearming must identify a new generation and disclose discarded unread history.
These are known timer API semantics validated on this implementation, not an OS
discovery or an allegation about existing runtime code.

**T.** Seven modes by three cyclic-order repetitions, 21 fresh exec'd workers.
Periodic interval 2,000,000 ns; initial absolute deadline 50,000,000 ns ahead.
First read is intentionally delayed until at least deadline +20 or +60 ms.
Periodic modes read again after at least another 20 ms of consumer silence.
One-shots return once despite delay, then EAGAIN. DISARMED gives EAGAIN.
SHORT_READ requests seven bytes (EINVAL), then eight bytes (one expiration),
then EAGAIN. REARM waits for an unread old one-shot to become readable, rearms,
checks predeadline EAGAIN, then reads one new expiration and EAGAIN. Actual
clock brackets, native raw bytes and callback receipts determine the result.
One formal invocation, zero retries/replacements/tuning; child timeout 3 s and
external supervisor timeout 20 s. Actual supervisor wall was 16.051661310 s,
including imports/process startup/serialization, not a timer-performance metric.

**D.** All 21 cases, source hashes, zero exits, exact error controls, raw uint64
counts, cumulative periodic clock bounds, one callback per successful read,
neutral authority and complete audit/mutation gates must pass. A complete
contract miss is FAIL; incomplete evidence or setup/timeout is HOLD/STOP. The
unsafe shadow remains failed even when the boundary hypothesis passes.

**C.** Same monotonic domain, single descriptor owner, no concurrent reader,
fixed integer-nanosecond schedule, explicit 8-byte native-endian unsigned
counter. Controlled delay is not natural workload incidence. The callback has
no acquisition cost or actual application state; no task, capture-quality,
latency improvement, CPU efficiency or response-time claim is possible.

**U.** Scheduling, host virtualization, clock accuracy and frequency are not
controlled. Linux6.18.44 x86_64/glibc2.41, CPython3.13.5; guest CPU AMD EPYC9V74,
allowed CPUs0-4; frequency snapshot2596.142MHz, not pinned. Python reports
CLOCK_MONOTONIC resolution1ns; resolution is not accuracy. No calibrated
combined uncertainty or coverage factor is available. Integer read brackets
are conditional accounting bounds, not statistical confidence intervals.
Provided execution container only: Docker/OrbStack CLI and image attestation
are absent. No install, experimental network, GUI/input or provider activity.

## Accounting derivation and variable table

| Symbol | Meaning / definition | SI unit | Domain / assumptions | Type |
|---|---|---|---|---|
| d | First absolute monotonic expiration time | s (stored integer ns) | Positive; same clock domain | Scalar time |
| p | Period between nominal expirations | s (stored integer ns) | Positive for periodic cases | Scalar duration |
| t | Monotonic instant used to count due expirations | s (stored integer ns) | Same domain as d | Scalar time |
| K(t) | Number of nominal periodic deadlines at or before t | 1 | Nonnegative integer; one armed generation | Integer scalar |
| a_i | Timestamp immediately before read i | s (stored integer ns) | Ordered, before or at b_i | Scalar time |
| b_i | Timestamp immediately after read i | s (stored integer ns) | Ordered, after or at a_i | Scalar time |
| r_i | Kernel read instant, not directly observed | s | Within read bracket | Scalar time |
| c_i | Unsigned count decoded from successful read i | 1 | Positive integer; 8 native-endian bytes | Integer scalar |
| S_i | Cumulative count through successful read i | 1 | Sum of c_j within one unchanged generation | Integer scalar |
| R | Number of actual callback receipts | 1 | One per successful 8-byte read | Integer scalar |
| N | Total reported expirations in the case | 1 | Sum of successful-read counts only | Integer scalar |
| M | Unobserved slots within reported expirations | 1 | N minus R; excludes discarded unread generations | Integer scalar |

The periodic deadlines form `d, d+p, d+2p, ...`. If t<d, none is due.
Otherwise, the largest nonnegative integer index not exceeding (t-d)/p is its
floor, and including index zero gives

`K(t) = max(0, floor((t-d)/p) + 1)`.

With one owner and no intervening rearm, each read drains the accumulated
counter. Therefore `S_i = c_1 + ... + c_i = K(r_i)`. Since the monotonic clock
brackets the kernel read, `a_i <= r_i <= b_i`, and K is nondecreasing,

`K(a_i) <= S_i <= K(b_i)`.

The auditor computes this separately from primitive timestamps and counter
bytes; it does not use nominal sleep length as observed time. Actual callback
cardinality is checked independently. The accounting convention is `M=N-R`.
If one read reports 31 expirations but invokes one callback, it gives one current
mock receipt and30 unobserved reported slots, not31 observations of the past.

**Dimension check:** (t-d)/p is dimensionless because numerator and denominator
are durations in the same units. K, c, S, N, R and M are counts (unit1). All
arithmetic is on integer nanoseconds before optional display conversion.

This is not a proof that the callback sampled any specified real-world instant,
nor proof of missing or absent GUI events. Timer counts cannot reconstruct
unacquired state. Rearm invalidates the unchanged-generation premise; the
separate discard marker prevents cross-generation attribution.

## Preservation and collision boundaries

Intake main `03ac3306861c2692b796bb14e2880ba9829d8291`. Root README, current goal,
roadmap, recent open/closed Issues, PRs and102 branch names were inspected.
#3934 owns the concurrent scheduler-attribution experiment, so it was not run.
A timerfd Issue search was empty before #4001. Search cannot see unpushed work.
Only `research/live_control/timerfd_observation_accounting_20260922_v1/` is added;
no runtime/default, old result, root index or other branch is modified.

The older chat-local #2547 experiment remains FAIL_MEASUREMENT_BINDING with
150 audit errors; it is distinct from #3934. Its supplied ZIP554448 bytes,
SHA256 `f6fcf01e9280871b761990528cb279c9f32b6f56c8207bf95e42291ac4fa5787`,
was restored read-only and all273 manifest entries verified. Its old audit
returned1 and reproduced the failure. The current environment still lacks the
required `/proc/<pid>/task/<pid>/children` inventory. No old timing was rerun
or promoted. This new bundle retains the old re-audit stdout, not the entire
older ZIP: complete old raw remains in the prior conversation download. The
old publication STOP is historical; GitHub write tools are available in this
conversation. This is retrospective disclosure, never backdated registration.

## Integration handoff / remaining roadmap

The validated constraint is to separate timer-expiration accounting from real
observation receipts, and retain a generation/discard boundary when rearming.
Operating-system instrumentation can expose unobserved slots; control systems
can treat that gap as uncertainty rather than fresh evidence; HCI/agent
interfaces can report observation coverage without converting timer activity
into a human/model-visible update. These are transfer ideas, not measured
benefits. A production adopter must validate its actual producer, acquisition
boundary, model-visible delivery, fallback and freshness requirements.

This experiment's scientific roadmap is complete. Delivery still requires the
additive PR, exact-byte readback and review/check gates. #2547, #3934, #57 and the
repository ROADMAP remain open. No generic scheduler or learned model is added.

## Revalidate without repeating the experiment

The publication contains readable frozen source plus a lossless, bounded
source/evidence archive. Run `python unpack.py /tmp/timerfd4001-audit` from this
directory with an absent destination. It only restores verified bytes, never
executes archived code. In the restored directory:

```sh
python -B audit.py formal-01
python -B test_audit.py --formal formal-01
python -B -m unittest -v test_audit
```

Expect audit PASS/errors0, corruption12/12 and unit5/5. Do not invoke
`study.py run` or repeat the historical allocation. Any future kernel/backend
or acquisition experiment needs a new ID, source freeze and independent gates.

## Primary API references

- CPython3.13 os timerfd documentation: https://docs.python.org/3.13/library/os.html#os.timerfd_settime_ns
- Linux man-pages, timerfd_create(2): https://man7.org/linux/man-pages/man2/timerfd_create.2.html

Absolute CLOCK_MONOTONIC deadlines use the monotonic clock's own domain, not
the Unix wall-clock epoch. The present claim is confirmed by retained raw
behavior and explicit implementation assumptions, not by API authority alone.
