# Outcome-query index tradeoff i6k2 — prospective plan

Issue #4396. Intake main `4c701cc51b06296268ad8d9ae3eff1dd6f2d379d`.
Only new path `research/verification/status_query_index_i6k2_v1/` and branch
`research/status-query-index-20260926-i6k2`. No shared runtime changes.

## Purpose and evidence lineage

The same model should not need to repeat uncertain actions to recover outcomes.
Before this application-specific research query can be used repeatedly, its
lookup cost must be understood. The earlier s8r1 study established result
semantics only. Its 797 original files were restored unchanged and its original
audit/controls and 18 tests passed; zero old scientific/GUI runs were repeated.
The whole old corpus is not included here. PROVENANCE.json pins the source ZIP
and the two reused modules. Neither query.py nor sink.py is modified.

This is known database physical-design engineering, not a novel algorithm,
production defect, full agent integration, or model/token-benefit experiment.

## H — one changed factor

An ordinary non-unique `commits(job_id)` index should preserve every output of
the unchanged read-only query and every measured append, including refusal of
inconsistent multi-commit evidence. At 32768 retained commits the median paired
indexed/plain complete-query total should be at most 0.50. Index creation,
storage and append maintenance are explicit costs, not assumed free.

## T — exact allocation

Resource study: history sizes 256, 4096, 32768; PLAIN and INDEXED; three fresh
worker repetitions. Arms alternate PLAIN/INDEXED, INDEXED/PLAIN, PLAIN/INDEXED.
One size per batch, six workers each. Total 18 workers.

Each worker creates the exact archived Store schema. In a single setup
transaction it directly populates a synthetic, internally consistent history:
job `bg-00000001` through `bg-N`, revision 1 through N, value `value-00000001`
through `value-N`, kind AUTO, session `i6k2-formal-N`, document doc, epoch epoch-1.
Job numbers are eight-digit zero-padded. Seen fingerprints are SHA256 of exact
sorted compact JSON requests. The document ends at revision N and the Nth value.
This is a generated input, not a claimed observed GUI history and not measured
Store.apply throughput. The indexed arm then executes exactly:

```sql
CREATE INDEX commits_by_job ON commits(job_id)
```

There is no UNIQUE constraint, changed query, LIMIT, skipped validation, or
post hoc removal of duplicate evidence. Logical table commitments before/after
index creation must be equal. Actual index list/columns and EXPLAIN QUERY PLAN
output are retained; the specific plan text is descriptive, not a hard gate.

Four queries: first, middle (integer N/2), last, and absent job. Two complete
warmup rounds are excluded. Eleven timed rounds rotate class order by the round
index. Total 792 timed queries, plus 144 excluded warmup queries. Timing wraps
the entire unchanged query(): request hashing, connection open, BEGIN/read-only
snapshot, all validation, COMMIT and close. Serialization, result retention,
imports, fixture generation and index construction are outside this endpoint.
Each call is one request, not a pre-opened connection benchmark. Hash actual DB
bytes before all queries and afterward; any byte change fails the read-only gate.

Afterward, 21 unique SUBMIT jobs per worker append revisions N+1 through N+21
through the unchanged Store.apply(), with values `append-value-00000001` etc.
These are private generated transactions, not uncertain input replay. Their
378 individual wall/CPU spans and complete before/after/results are retained.
Index build time, seed/index/final DB bytes, page count/size and final logical
content commitment are mandatory costs.

Contract study: two fresh workers, one per schema, ten private databases each.
Applied, stale, conflicting revision, same-value no-op, absent, altered request,
invalid epoch, deliberate duplicate commit, deliberate missing commit and
unknown stored status. The latter inconsistent histories are labelled controls,
not naturally observed storage corruption. Full pre-query SQLite bytes are
retained for these 20 fixtures. Query outputs and before/after hashes must agree
with an independent relational oracle. Invalid epoch must open no DB.

Construction uses only size32, one repetition per schema, and the ten contract
fixtures per schema. Its outputs and 12 read-only regression tests are excluded
from all formal denominators. Type-sensitive comparisons and ten effective
mutation controls are checked before source freezing.

## Execution and stopping

All source, plan, environment, corpus recipe and auditor bytes must be committed
and read back through GitHub before formal batch0. A public hash alone is not
called full source publication. If that prerequisite fails, do not run formally.

Four separate synchronous commands, in order, each exactly once:

```sh
python -S -B run.py --out formal/batch-0 --batch 0 --phase formal
python -S -B run.py --out formal/batch-1 --batch 1 --phase formal
python -S -B run.py --out formal/batch-2 --batch 2 --phase formal
python -S -B run.py --out formal/batch-3 --batch 3 --phase formal
```

Each batch requires the previous successful END and actual outer exit receipt.
Worker deadline 8s, inner batch budget30s, outer limit35s. Output destinations
are exclusive. Every worker output, stderr, exit, PID, argv and time bracket is
retained immediately. Any incomplete/nonzero batch ends allocation. No retries,
replacement, pooling, deletion of outliers or source/gate tuning after results.
Construction fixes are separate retained engineering records, not new Issues.

## D — separate correctness, performance and adoption decisions

PASS_QUERY_INDEX_SEMANTICS_SCOPED requires all18 workers,792 timed query outputs,
378 appends,20 contract fixtures and actual process/batch receipts; exact source
closure; all input/result/table commitments; read-only byte equality;
non-unique indexing; explicit unknown/conflict/refusal semantics; an independent
raw-only audit; and at least8 effective well-formed evidence mutations rejected.

PASS_LARGE_HISTORY_QUERY_TIME_SCOPED separately requires the median of three
paired INDEXED/PLAIN 44-call wall-total ratios at32768 to be <=0.50. A complete
miss remains HOLD_QUERY_TIME_BENEFIT; no favourable subset rescues the gate.
Report per-size/class descriptive medians and ranges, all samples, index build
and storage, and append cost. There is no predefined write-workload distribution,
so a lookup PASS alone cannot justify production adoption or universal break-even.
Semantic contradiction is FAIL. Missing source/process/coverage/control integrity
is HOLD/STOP. All original first outcomes remain immutable.

## Evidence contract and independent reconstruction

Large SQLite files are deterministic generated workload inputs. Their literal
redundant copies are kept locally, but are NOT promised in repository evidence.
Publish the full frozen recipe, actual physical hashes/sizes, all logical-content
commitments, SQL metadata/plans, every observed query/append output and timing,
and complete actual process records. This is explicit input regeneration, not
recreating or fabricating observed timings. Small contract DBs are literal bytes.

A logical commitment streams the table name plus LF and each compact JSON row
plus LF, ordered document.id, commits.ordinal, seen.job_id. The auditor generates
the expected complete history independently and compares every observed table
commitment; it does not import worker.py/query.py/sink.py. It also reads literal
small DB bytes independently. Same-author separate implementation/process is not
external human review. Integrity hashes are not source authentication.

## Conditional preservation argument

The added non-unique index introduces no predicate, uniqueness requirement,
changed table row, or alternative result projection. SQL selects all rows for
the same job ID and orders them by the unique INTEGER PRIMARY KEY ordinal.
For an unchanged logical table, both physical access paths therefore select the
same ordered rows. The same pure postprocessing gives the same response. This
argument assumes SQLite implements its documented index/SELECT semantics and
there is no concurrent modification between the compared inputs. Actual native
query outputs and duplicate-evidence controls test this composition; the proof
does not establish a speedup.

Index maintenance adds work/storage. Reducing a particular SELECT's scan cost
need not reduce the full query proportionally because hashing, open/close and
other validation remain. End-to-end agent benefit depends on the application's
actual history sizes, query/write mixture and model latency, none measured here.

## Variables and dimensional check

| Symbol | Meaning (Japanese) | SI unit | Definition/domain | Type |
|---|---|---|---|---|
| N | 事前の保存履歴件数 | 1 | 256,4096,32768; construction32 | integer scalar |
| R | 新規プロセス反復番号 | 1 | 0,1,2 | integer scalar |
| K | 照会クラス | 1 | 0=first,1=middle,2=last,3=absent | categorical scalar |
| T | 44照会の壁時計時間合計 | s | sum of monotonic end-start, converted ns to s; positive | real scalar |
| C | CPU時間 | s | process_time_ns end-start converted to s; nonnegative | real scalar |
| rho | 索引あり/なし時間比 | 1 | paired T_indexed/T_plain; positive | real scalar |
| B | 保存容量 | 1 (bytes, non-SI information unit) | actual file size; nonnegative integer | integer scalar |
| q | 要求 | not applicable | seven-field JSON object with strict identity/content types | record |

Clock values are recorded in ns, converted by division by 1000000000 for SI
seconds (by1000000 for reported ms). Endpoints are subtracted only within the
same monotonic or process clock. rho divides two equal time units and is
dimensionless. Byte counts are information quantities, not seconds or disk I/O.

## C / U and environment

Actual ENVIRONMENT.json is authoritative. Supplied Linux x86_64 container,
CPython3.13.5, SQLite3.46.1, standard library, DELETE journal/FULL synchronization.
No Docker/OrbStack engine/image attestation; no GUI/input/model/provider/user-data
or external-network experiment, package install or production mutation. Workers
are affined to one allowed logical CPU; host exclusivity and frequency are not
controlled. Warm local files, new per-call SQLite connections, same generated
input per matched pair. Three process repetitions are descriptive, not calibrated
confidence/tail bounds. Clock resolution is not accuracy; combined timing
uncertainty and coverage factor are not estimated.

The query's trusted database identity, honest complete receipt history and
quiescent comparison assumptions remain. No crash/retirement/restart/multi-owner,
malicious storage, external-effect atomicity, general outcome completeness,
model-usefulness, token savings or integrated product acceptance is established.

## Sources and roadmap

Primary specifications: SQLite Query Planning
(https://www.sqlite.org/queryplanner.html) and CREATE INDEX
(https://www.sqlite.org/lang_createindex.html), consulted2026-09-26 JST.

Source/intake -> excluded construction -> full public freeze/readback -> fixed
allocation -> raw audit/effective controls -> reviewable declared-evidence PR ->
exact-head applicable checks and scoped review -> qualified research-only main
merge/readback -> only supported dependency-safe owned branch cleanup.
Global ROADMAP, #24 and #2789 are not completed by this bounded experiment.
