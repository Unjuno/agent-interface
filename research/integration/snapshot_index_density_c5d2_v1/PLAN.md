# Fixed-byte snapshot index density — c5d2

## Question / scope / chronology

Related to #3985 and the conversation-local b7e1 snapshot result. The b7e1
archive explicitly says its full-drain peak is not resident index cost. This
study holds input size constant and varies record density to measure retained
preparation allocations. No new pager is implemented. The exact archived
FrozenSnapshot is unchanged. #4068 owns demand-index first-return/drain timing:
this worker stopped its overlapping draft before freeze/formal (0 cases),
retaining nine unit tests and three excluded smoke workers separately.

Intake main 2308b8301d69b7089a2e0636486736ed59b61537. README, CURRENT_GOAL,
ROADMAP, recent open/closed Issues, open PRs, branch pages (138 names across
non-atomic calls), #4012, current reader, snapshot/index and lazy searches were
read via GitHub MCP. A later branch read exposed #4068, so no exhaustive/no-other-
worker claim is made. Targeted snapshot+density Issue search returned no match.
No source/branch/Issue belonging to another worker is modified.

Owned new proposed path: research/integration/snapshot_index_density_c5d2_v1/.
Proposed branch: research/snapshot-index-density-c5d2-20260922 (local only).
There are no GitHub write actions or gh/token here; this is a LOCAL prospective
freeze, not GitHub preregistration. Publication limitations stay with the
originating question's evidence, not a wrapper-only successor Issue. Existing
Issue states do not establish product acceptance. #4012 remains Draft/held.

## H / T / D / C / U

H: For the unchanged eager index, a constant 1 MiB immutable input cap does not
imply constant metadata allocation. Higher line density creates more prefix
entries even when only32 records will be read. Across the fixed9 cases, median
retained Python allocation after preparation at8192 records is at least8 times
that at128 records. This threshold concerns a bounded fixture/CPython snapshot,
not RSS or a production memory budget.

T: Three count conditions128/1024/8192, each exactly1,048,576 input bytes, three
fresh processes per condition. Valid fixed-width JSONL, width8192/1024/128 bytes
respectively, including LF and whitespace padding. First32 record values are
identical across conditions. Rotate order by repetition:128,1024,8192;
1024,8192,128;8192,128,1024. Minimum sample count3 per cell,9 total. No seed/random
race. One formal parent, fresh exclusive output, each child10s bound, parent25s
bound under a40s tool call. Preserve first outcome, source/input/raw bytes and
actual waits/exits. Missing/failed child ends this allocation without retry.

Trace scope: create input bytes and import code BEFORE tracing; full GC;
tracemalloc.start(1); exact FrozenSnapshot.prepare; full GC; take one snapshot;
stop tracing. Retain every live trace's size/domain/source/line. The input bytes
are deliberately excluded because preexisting. No query occurs during tracing.
After stopping, inspect exact index entries and call read(max_records=32).
The trace sum measures blocks allocated during preparation that remain live at
snapshot time, including minor harness/tracer-visible overhead. It is NOT peak
memory, process RSS, total Python memory, or tracemalloc's own storage. Input
storage, query response allocations, file I/O and serialization are excluded.
Also report sum attributed specifically to eager_snapshot.py as a diagnostic.

D: PASS_INDEX_DENSITY_MEMORY_SCOPED only if all9 first cases have exact source,
fixed byte count, valid input, index entries/count/prefixes, page output/current
cursor and historical/authority-neutral metadata; all raw trace sums/types,
commands, actual zero exits and no stderr reconcile; independent raw-only audit
and10 declared semantic corruption controls reject; median trace ratio>=8.
Complete valid magnitude miss is HOLD_DENSITY_MEMORY_MAGNITUDE. Semantic error is
FAIL_INDEX_CONTRACT; missing source/raw/exit/provenance is STOP/HOLD. No missing
exit is inferred and no repeated sample is added to get a favorable ratio.

C: Padding controls byte count but changes individual line length and count;
that is the declared density factor, not real-workload distribution evidence.
Python object layout, allocator reuse, trace attribution and GC affect values.
tracemalloc can omit memory outside Python allocators. Counts and exact prefix
identities are independently reconstructible; actual allocation sizes are
observations from the tracer, not independently reproduced allocator behavior.

U: 3 repeats are descriptive median/range, not tail estimates or reliability.
No calibrated combined uncertainty u_c or coverage factor k is available; do not
invent them. Source bytes are bounded, but a finite maximum line count also
implies a finite implementation-dependent metadata bound. This study must NOT
claim unbounded memory or an OS/security vulnerability. No model/provider,
GUI/input, user documents, experiment network, package installation, production
runtime/default changes, engine-attested Docker/OrbStack or global completion.

## Complete conditional argument and variable table

| Symbol | Meaning | Unit (SI / information) | Definition | Domain / assumptions | Type |
|---|---|---|---|---|---|
| D | immutable input byte sequence | byte (non-SI information unit) | exact fixture bytes | trusted bytes, fixed during preparation/read | byte vector |
| S | input length | byte | len(D) | formal1,048,576 | nonnegative integer scalar |
| N | complete records / LF boundaries | 1 | number of terminal LF bytes | formal128,1024,8192; no embedded literal LF | positive integer scalar |
| W | fixed record width | byte | S/N | integer, includes LF | integer scalar |
| j | boundary ordinal | 1 | zero boundary plus complete records |0..N | integer scalar |
| B_j | boundary byte offset | byte | jW |0..S | integer scalar |
| P | first page limit | 1 | caller max_records |32 | positive integer scalar |
| E | retained index entries | 1 | cardinality of prefixes | N+1 after prepare | integer scalar |
| H_j | prefix digest | none /256-bit digest | SHA256(D[:B_j]) | exact prefix; integrity not authentication | bit vector |
| a_i | size of recorded allocated block i | byte | tracer size field | positive integers at one snapshot | integer scalar |
| K | recorded live allocation blocks |1 | trace-row count | finite, environment-dependent | integer scalar |
| M | retained tracked allocations |byte | sum of a_i | excludes pre-trace bytes/RSS/tracer storage | integer scalar |
| R | high/low median allocation ratio |1 | median M at8192 / median M at128 | positive denominators,3 repeats/cell | real scalar |

The constructor starts with table{0:(1,SHA256(empty))}. Thus E=1 before scanning.
For j from1 through N, the next LF terminates exactly the j-th record at B_j.
The loop adds one distinct key B_j because W is positive and B_j>B_(j-1).
No entry is removed. The update consumes only D[B_(j-1):B_j]. Repeated SHA256
updates equal hashing their concatenation (Python hashlib contract); induction
therefore yields H_j=SHA256(D[:B_j]) and sequence j+1 at each entry. Base j=0
holds by construction; the induction step appends one disjoint slice and adds
exactly one key. Consequently E=N+1 at return. The caller's P is not an argument
to prepare and cannot change this entry count; a later read only consults it.
For valid records the first-page cursor is offset B_min(P,N), sequence
min(P,N)+1 and digest H_min(P,N), with limit tail when P<N. Neutral flags follow
the unchanged read function. Independently reconstruct every formal prefix.

A fixed S bounds input bytes, not a constant entry count: our three valid W
values give E129/1025/8193 at the SAME S. Every retained entry occupies positive
implementation storage, but this argument does not specify exact byte totals
or prove the factor8 threshold. The remaining claim is empirical through the
retained traces, not assumed from the theorem. It also does not claim infinite
memory: for byte data N<=S, so E<=S+1 under a fixed cap.

For trace rows, M=sum(i=1..K,a_i). Audit recomputes M from raw rows and separately
sums the rows whose recorded filename is eager_snapshot.py. R is computed from
three-value medians; no discarded sample or statistical tail is used.

Dimension check: N and j are dimensionless, W is byte, hence jW is byte as
required by offsets. E=N+1 is a count. Every a_i and M have byte units; the ratio
of two M medians is dimensionless. One MiB is1,048,576 bytes (not an SI prefix).
Numerical index example: at S1,048,576 and N8192, W128, E8193, first32 cursor
is4096 bytes with sequence33. At N128, W8192 and the same page uses262144 bytes.
This is structural arithmetic, not a fabricated memory benchmark.

ERROR CHECK before formal: unchanged source Git/hash identity, finite valid
fixtures, disjoint construction, safe output paths, raw sum/response oracle,
corruption sensitivity and process exit records. Recheck source after execution.

## Roadmap

Prior archive re-audit (done); preserve overlap STOP (done); verify density scope;
excluded trace construction; freeze source/plan/environment; execute9 first
cases; raw-only audit and mutations; retain full source/raw/report and additive
patch; repository publication/current-head review/CI/main readback only when the
actual write path exists. No duplicate demand-index performance allocation.

## Primary references

Python3.13 hashlib update semantics: https://docs.python.org/3.13/library/hashlib.html
Python3.13 tracemalloc measurement scope: https://docs.python.org/3.13/library/tracemalloc.html
GitHub exact reader: blob ea72c166c2cea511ea91031dfbb14563fe4e3245.
Predecessor snapshot SHA256 b3f4e81be3389b40cccb6b435e1f6bc1ded1bf0697312475a54523d430001232.
Official docs currently render3.13.15; the executed interpreter is3.13.5, recorded
in ENVIRONMENT.json. No external performance numbers are used.
