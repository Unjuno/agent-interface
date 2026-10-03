# V2 terminal scope of retained #6907 traces

This is post-hoc analysis of the original immutable raw, not a new source-arm
or formal allocation. PLAN.json and FREEZE_V2.json were written before this
reader's actual invocation. Each original event and first outcome is retained.

For a period P=100,000,000 simulated ns and cutoff t, enumerate grid points
kP with integer k>=0 and kP<t. An emitted sample's current slot is its declared
scheduled point plus P times missed_periods_before; those preceding points are
explicit skips. Any interior point in neither set is unrepresented in emitted
receipt accounting. Equality with t is excluded. This diagnostic does not
define a replacement runtime counter or manufacture catch-up samples.

| Arm / original outcome | Rows | Rows with unrepresented interior points | Maximum points |
|---|---:|---:|---:|
| original / complete | 122 | 19 | 64 |
| repair_v2 / complete | 256 | 130 | 65 |
| one_command / complete | 256 | 72 | 2 |
| original / diagnostic budget stop | 134 | 64 | 1 |

The original assay captures emitted receipts, not terminal stats. This table
therefore does not assert measured values of returned missed_sample_periods.
The old abstract reference agrees with source-policy receipt fields; it is not
an independently justified whole-terminal-grid measurement oracle. The source
owners' later #6896/#6913 evidence is attributed separately. Revised #6913
is not imported, executed or evaluated here, and its retained-current-slot skip
convention is not replaced by this diagnostic. An actual session's direct final
sample can carry additional information absent from these standalone traces.

All768 original start-age scalars match separate event recomputation. The
90 original age contrasts and all64-sample censors stay unchanged. In particular,
one_command reduces the largest age yet still has72 complete traces with an
unrepresented terminal interior point; age improvement is not complete feedback
accounting, physical observability or useful control.

Six declared literal grid expectations and three malformed-record negatives
ran first, then the pinned original raw reader ran once. Receipts retain actual
UTC and exit0. New helper snapshots have .py.txt suffixes. No old producer,
auditor, copied controls, compatibility suite, game/model/GUI/native input,
container, shared resource or formal allocation was invoked.

| Symbol | Japanese meaning | Unit | Type / definition |
|---|---|---|---|
| P | 仮想サンプル周期 | simulated ns | positive integer;100,000,000 |
| t | 保持された最終イベント終了時刻 | simulated ns | nonnegative integer |
| G | 終了より前の名目周期点 | simulated ns per element | finite set;kP<t |
| U | サンプルと明示スキップに現れない周期点 | simulated ns per element | finite set;G minus represented slots |

No real duration or SI host-time performance estimate follows from simulated
integer costs. Full measurement-auditor, source admission, live feedback/task
effect, release and deployment gates remain open. V2 is a known-fault research
archive requiring new content votes; older votes and private never-sent apply
candidates are preserved, not automatically reused.
