# SQLite prepared-statement cache / per-intent dependency receipts

Allocation: `sqlite-readset-cache-20260922-01`.
Origin: open #1713 automatic read-set reconstruction, closed #501 observed read
receipts. This is a NEW real-SQLite adapter experiment, not a rerun of either
Issue, a production vulnerability claim, or an access-control experiment. All
SQL is fixed and all authorizer callbacks return SQLITE_OK. Only disposable
application-owned data is used.

Publication status at freeze: local preregistration only. This connection has
48 GitHub GET/search tools, no write action; gh/docker/podman and configured
GitHub credential variables are absent. Directory search found no alternative
write-capable installed GitHub connector. Do not invent a remote Issue number,
GitHub pre-registration, branch, PR or merge. Intended additive branch:
`research/sqlite-readset-statement-cache-20260922`.
Intended additive namespace: `research/integration/sqlite_readset_statement_cache_v1/`.

## H — falsifiable hypothesis
Using a compile-time SQLITE_READ callback as if it were a per-execution read
trace loses dependencies on warm Python sqlite3 statement-cache hits. In the
fixed singleton-table family, this permits publication of a cached decision
whose source value changed after preparation. Disabling SQL statement caching
prevents that omission, but may collect conservative extra dependencies.

Reusing only connection/schema/SQL-bound observed dependency metadata, while
reacquiring value revisions in the same read transaction on EVERY execution,
preserves the stated freshness and precision conditions for the frozen corpus.
The metadata contains table identities, NEVER a reusable value/version token.
Missing metadata yields UNKNOWN and no effect (separate unit control).

## T — actual environment and finite corpus
Provided Linux x86_64 execution container, CPython3.13.5 / SQLite3.46.1.
Exact interpreter, extension and libsqlite3 SHA-256 identities in ENVIRONMENT.
No Docker/OrbStack image/engine assertion, install, GUI/input/model/provider,
external experiment network, existing user data or shared runtime edits.

Three arms: EVENT_ONLY (`cached_statements=128`, reset callback log each intent),
NO_STATEMENT_CACHE (`cached_statements=0`), METADATA_REUSE (`cached_statements=128`,
connection-local metadata keyed by schema cookie and exact SQL).

Ten scenarios, two fresh deterministic repetitions per arm =60 databases:
cold stable/change; warm stable/change/unrelated/rollback/change-before-prepare;
different SQL after warm; view retarget followed by new-table or old-table change.
Scenario details and partly rotated arm order are fixed in SCHEDULE.json.
There is no random-race or population-rate inference, nor balanced performance
benchmark. Each formal case uses a fresh reader worker and a separate resident
writer/observer peer; the peer opens a new connection per request, mode=ro for
observations. Request/response barriers choose the order, not sleeps.
Preparation reads value and revisions in one BEGIN transaction. Validation and
private effects-table insert occur in one BEGIN IMMEDIATE transaction. Writers
update value+revision in one transaction; rollback leaves both unchanged.

Ten consecutive batches, six first cases each. One foreground supervisor per
batch, 30-second internal ceiling and 40-second outer-tool ceiling. Worker
12-second and peer-response3-second ceilings. Source/runtime identity gates
precede every formal batch. A failed batch is terminal; never resume, replace
or pool it. Each next batch requires the prior actual zero exit and chained
execution hash. Capture stdout/stderr, actual worker/peer/outer exits, commands,
SQL traces, callbacks, revisions, observer snapshots, final database and hashes.

## D — preformal decision gates
Scientific PASS_SQLITE_READSET_CACHE_BOUNDARY_SCOPED requires all60 exact rows,
all10 actual outer exits, all120 worker/peer exits, source/runtime identity,
independent raw/database audit errors0, and8 case-level semantic corruption
controls rejected after each intact relocated baseline passes.

EVENT_ONLY: exactly10 missing-dependency rows and2 stale private commits expose
the registered compile-vs-execute contrast. These are failures of the explicitly
constructed comparison, NOT assertions about upstream production code.

NO_STATEMENT_CACHE: missing dependencies0 and stale commits0; report all false
refusals rather than require precision. METADATA_REUSE: missing dependencies0,
stale commits0, false refusals0, metadata reused on10 current executions. Warm
change-before-prepare must carry revision2, not reuse its primed revision1.
View retarget must bind the current resource and schema.

Complete contrary outcomes are FAIL_BOUNDARY_HYPOTHESIS; missing data/source,
process/timeouts or audit ambiguity are STOP/HOLD. No postformal source, gate,
scenario, repetition or result tuning. The source table is singleton-only;
view output and final private effect are independently checked from raw DB.

## C — construction-informed design and limits
The original proposed NO_STATEMENT_CACHE precision gate failed in the30-case
construction: an altered view produced callback entries for both a and b,
although its evaluated value came from b. The old-table change therefore
caused one false refusal. This observation is preserved in CONSTRUCTION_AUDIT
and motivates reporting this secondary outcome WITHOUT hiding or repairing it.
The primary METADATA_REUSE and omission gates are unchanged. Formal plan is
construction-informed, not blind or independent-site replication.

Callbacks describe compiled table/column access, not row-specific dynamic data
or control dependencies. Exact-SQL/schema metadata may overapproximate when
initial preparation and schema recompilation produce more than one access set.
This candidate is not claimed minimal for arbitrary SQL, connections, UDFs,
attached DBs, virtual tables, views, row predicates or bypassing writers.
Connection confinement and schema-cookie checks are assumptions, not security
isolation. No broad parent Issue or roadmap is closed by the finite result.

## U — uncertainty and stop
Counts, exact strings and integer revisions determine gates. monotonic_ns is
for ordering only; CPU frequency/host contention are unmeasured and uncontrolled.
No calibrated combined timing uncertainty (u_c) or coverage factor k is defined
because no physical performance estimate is reported. No confidence interval
or general failure rate is inferred from two authored repetitions per cell.
No cache latency/token gain, automatic GUI dependency discovery, authority,
crash/power-loss durability or product acceptance follows.

## Bounded roadmap
1. Read current goal, Issue/PR/branch state and official callback contract.
2. Excluded construction, preserve its timeout and instrumentation/gate failures.
3. Freeze source, environment,60-row schedule and decision gates locally.
4. Execute ten immutable six-case batches with actual exit receipts.
5. Independent raw-only database audit,8 semantic corruption controls,8 unit tests.
6. Report evidence, additive patch/capsule and explicit publication blocker;
   remote Issue/PR/main only if a supported write path becomes available.
7. Recheck main; do not delete any foreign or unpublished branch.

## Variables and units
| Symbol | Meaning | SI unit | Definition | Range / assumptions | Type |
|---|---|---|---|---|---|
| q | Fixed SELECT query | 1 | One key of policy.QUERIES | Exact SQL, one singleton value | Discrete scalar/string |
| D | Captured source-resource identities | 1 | Observed metadata selected for q | Subset of {a,b,u}; schema separately bound | Finite set |
| r | One resource identity | 1 | Member of D | Application-owned singleton table | Discrete scalar |
| v_p(r) | Revision read at preparation | 1 | Stored revision in same snapshot as value | Positive integer; cooperative monotonic update | Integer scalar |
| v_c(r) | Revision at commit check | 1 | Revision in BEGIN IMMEDIATE transaction | Same resource and connection database | Integer scalar |
| s_p,s_c | Prepared and checked schema cookie | 1 | main.schema_version at two boundaries | Integer; fixed trusted DB lifecycle | Integer scalars |
| x_p,x_c | Prepared and current source value | 1 | Singleton text payload at the two boundaries | Exact strings, not physical measurements | Discrete scalars/strings |
| t | Diagnostic monotonic timestamp | s | Recorded integer nanoseconds divided by10^9 | Same container clock; not calibrated latency | Real scalar |

Dimension check: revision/schema comparisons and all counts are dimensionless.
Ordering uses timestamps from the same nanosecond clock; no clock-domain mixing.
