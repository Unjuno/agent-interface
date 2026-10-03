# Accepted authorization versus later execution admission

Worker `01a0ff58-480b-7d50-9eee-0bce12250476`, FINAL-v5; parent #5215.
Source main `2c0c1183b861519fde7c71462a589fb904c3451e`.
New branch `research/kernel-authority-begin-order-01a0ff58-20261003`.
Ordinary host construction/proof checks only; no consumed formal allocation.

## Question and scope

The current kernel remembers accepted execution begin, but does not remember
the `now_ns` of successfully accepted authorization. Can two authorization
histories leave identical current lifecycle fields, yet require different
decisions when the same caller-supplied begin time is checked for chronology?
This is consistency of typed sequential evidence in one explicitly comparable
synthetic clock. It is not physical execution, truthful clock sampling or a
claim that a conforming monotonic-clock caller has a demonstrated failure.

H: With identical observation/binding/lease, authorization at 200 versus 400
leaves identical fields in current source. Begin at 300 is admitted in both.
An existing-observation floor of 100 cannot distinguish these histories.
Remembering accepted authorization time can distinguish them and refuse
before-grant begin times while preserving equal/later and existing refusals.

T: Test-first boundary regressions against exact original Git copies. Preserve
the first baseline failure. Then freeze two isolated full-source candidates:
(1) compare begin with existing observation capture; (2) remember successful
authorization separately and compare begin with that value. No runtime/kernel
file is changed. Execute one new ordinary finite matrix in fixed order:
baseline, observation_floor, authorization_floor; grants 200/400; begin values
0/99/100/199/200/300/399/400/1000; matching/nonmatching typed requests. Thus
36 rows per arm, 108 total. Same input values and source for all arms except
the declared candidate lines. Independently reconstruct all rows from data
with an auditor importing neither fixture, kernel nor candidate. Inspect the
two grant histories at begin=300 as the indistinguishability witness.

Boundary methods cover stale/equal/later begins, refusal then correction,
failed authorization and retry, existing binding mismatch and duplicate begin,
invalid caller clock types, existing receipt/cancellation/release lower bounds,
and cancellation without any accepted begin. Candidate boundaries and exact
current kernel regression suite run normally and with Python -O. The original
43-test source result already exists and may be reused only after checking all
nine source/test Git bytes against the previously tested copy. A current-base
source change is not silently relabeled as that original result.

D: PASS_ORDER_MEMORY_SCOPED only if all 108 unique ordered cases are present,
typed fields and expected outcomes match, every refusal preserves all fields,
and equal/later matching cases remain accepted before lease expiry. The memory
arm admits zero begin times before accepted authorization. The two stateless
arms have identical complete before-state for grants 200/400 and admit both
begin=300 requests; the memory arm differs only in retained grant time and
admits the earlier-grant history only. Every effective copied-data corruption
must be refused. Incomplete source/rows/process receipts or ineffective controls
means HOLD, not PASS. No threshold is selected after observing data.

C: The observation-floor comparator uses already available information and is
stronger than checking only nonnegative time and lease expiry. It introduces
capture-clock comparability in this fixture and still cannot recover a forgotten
authorization time. A trusted monotonic caller is the simplest no-added-state
alternative: honest sequential same-clock readings already impose chronology.
Do not claim equal-information performance superiority of memory, nor that
one integer is the only implementation. An externally supplied valid-from
bound or stronger clock contract would change the information available.

U: Finite authored timestamps, trusted dataclass values, immutable source, one
sequential lifecycle and common comparison clock only. No backend, model,
OS input, GUI, GPU, container, WSLc, concurrency, hostile public-field mutation,
clock-domain provenance, task-effect, release-after-final-action or performance
claim. Receipt end/release may be after lease expiry; no end cutoff is inferred.
The old #5216/#5225/#5229 records remain unchanged and HOLD stays HOLD. #6875
nominal types and #6894 cancellation uncertainty remain separately owned.

## Execution and preservation

The new eight boundary methods are ordinary reversible implementation checks.
Baseline failure precedes candidate construction. Final source/helper freeze
precedes the 108-row matrix. Preserve every child command/start/end/exit/stream,
first result, raw and failed setup/checker output; repair ordinary helpers with
versioned records. No producer/matrix rerun merely to repair an audit. A new
source/condition experiment needs a separate explicit difference and freeze.
Source, synthetic raw and candidate remain additive and non-executed by default.
All helper names are explicit check/audit/fixture entrypoints; copied kernel is
.txt, and no workflow or test-discovery entry is added. Dynamic votes/application
records belong outside this tree. Runtime promotion needs separate coordination,
content agreement and current-tree application; this package grants none.

| Field | 日本語の意味 | SI単位 | 定義・範囲・前提 | 型 |
|---|---|---|---|---|
| grant_ns | 承認が受理された呼出しの時刻 | ns = 10^-9 s | 合成共通時計、200/400 | integer |
| begin_ns | 実行開始に渡す時刻 | ns = 10^-9 s | 同時計、上記9値 | integer |
| captured_ns | 既存の観測時刻 | ns = 10^-9 s | 全条件で100 | integer |
| valid_until_ns | leaseの有効期限 | ns = 10^-9 s | 全条件で1000、開始は未満 | positive integer |
| authorized_ns | 候補が保持する受理済み承認時刻 | ns = 10^-9 s | 未承認None、成功後grant_ns | optional integer |
| accepted | 実行開始が受理されたか | 1 | True/False、OS入力ではない | boolean |

All inequalities compare authored times with the same units. No measured
nanosecond precision, physical elapsed time or latency estimate is claimed.
