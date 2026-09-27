# Dependency-scoped continuation during unresolved application effects

**Disposition: retain a scoped 75-case native-GUI calibration and two candidates. Do not promote a production-runtime, model, Doom, or general GUI speed claim.**

Task `O3-CROSS-DOMAIN-PENDING-FRONTIER-001`, Issue #93. Immutable base `a74c5cb704c17bc63e6d73aa98a4bac62d738c47`. Only new path `research/cross_domain/pending_effect_frontier_v1/` is modified.

The complete local plan and seven executed/test source hashes were bound by GitHub commit `734a07200b1bdd130dc3873838e459f6329fc10c` **before the first measured case**. `FROZEN_PLAN.json` records that receipt. The complete local `preregistration.json` is SHA-256 `f086a2dcdee5434651dd9650eb4e0406a8658df3e0015a10ab5debd3c80f2064` (8,433 bytes). All three blocks were executed once and completed. Construction runs are separate, not pooled.

## What is being explored

Prior cross-domain work showed that an unresolved side effect cannot safely be retried merely because input has been released. However, globally blocking the agent is unnecessarily restrictive when other tasks genuinely do not depend on that side effect.

Two new-to-this-lane candidates were tested:

1. **Dependency-scoped continuation (`frontier`)**: compare declared read/write resources against every unresolved operation, using canonical resource IDs. Keep dependent work pending but permit independent work. Fresh physical input checks still run before each actual input; the scheduling advice grants no input authority.
2. **Read-only reconciliation (`frontier_lookup`)**: the same frontier may request a bounded public application status lookup for the original operation. A matching committed-effect receipt can resolve lost acknowledgement. An absent record is **UNKNOWN**, not proof of no present or future effect, and never authorizes a retry in this experiment.

These build on established effect-system/noninterference and transaction ideas. They are not claimed as globally new concurrency algorithms. The experiment tests their use at an agent's asynchronous application-effect boundary, not a new language type system.

## Actual apparatus and fixed workload

Each case launches a fresh Tk application and SQLite database on an isolated Xvfb/Openbox desktop. Only real XTEST F1--F4 key presses request effects; F5 requests a read-only status lookup. A separate X11 connection samples focus, actual key down and empty release. Keyboard input remains serial; only application work overlaps. There is no concurrent multi-agent keyboard ownership.

The application is not given the policy name. It publishes the same effect/alias manifest and operation receipts to every arm. The controller does not open its scoring database. A separate retained-file audit reads the database after the policy loop and GUI process terminate.

The workflow has four operations: A produces an updated document, D reads A and later writes a report, B and C write unrelated documents. Request order is A,D,B,C, but a frontier can skip blocked D to run B and C. D snapshots its source when the GUI request arrives; its final database row therefore reveals a premature read. A,B,C each store an exact case-bound token. No application deduplication is present and no operation is retried.

| Condition | Executed value |
|---|---|
| CPU / affinity | Intel Xeon Platinum 8573C / logical CPUs 0--4 |
| Clock frequency | Not pinned or calibrated; shared-host scheduling |
| Python / kernel | CPython 3.13.5 / Linux 6.18.44 |
| Database | SQLite 3.46.1; DELETE journal; synchronous FULL; explicit BEGIN IMMEDIATE/COMMIT |
| GUI / input | Tk 8.6 series, private Xvfb/Openbox, real XTEST, nominal 10 ms key hold |
| Artificial application delays | A 240 ms, D 20 ms, B 100 ms, C 100 ms |
| Observation budget | 650 ms from policy-loop start |
| Status lookup | First at 280 ms, then at least 50 ms apart, at most 5 |
| Receipt polling | Nominal 2 ms sleep when no operation is eligible |
| Allocation | 5 scenarios x 5 policies x 3 repetitions = 75 fresh cases |
| Order | Three predeclared 25-case blocks; fixed seeded scenario shuffle and cyclic policy rotation; not full counterbalance |
| Timing | Same-host CLOCK_MONOTONIC/perf_counter_ns; reported 1 ns resolution is not accuracy |
| Model calls / Doom episodes | 0 / 0 |
| Production Agent Interface Executor/InputOwner | Not integrated |

Scenarios: ordinary delayed completion, an alias of the same A resource, lost A acknowledgement after commit, A request dropped before commit with no reply, and an opaque/unknown A read/write manifest. All policies see the same public conditions. The private oracle is used only for evaluation.

## Results: calibration success is not universal task success

Every one of the **75 expected-outcome audits** passed, including expected failures in unsafe controls. There were **285 independently empty input releases**, **930 valid input-state acquisition brackets**, and no repeated mutating operation in the measured cases. Full public receipt identities, input/application request counts, actual SQLite rows, document versions and exact contents were checked.

| Policy | Cases | Exact complete workflows | Incorrect report outputs / premature reads | Correct committed effects | Independent B/C completions before A resolution or censoring |
|---|---:|---:|---:|---:|---:|
| Global wait | 15 | 9 | 0 | 39 | 0 |
| Release-only continuation | 15 | 0 | 15 | 42 | 30 |
| Name-only frontier | 15 | 6 | 3 | 48 | 24 |
| Canonical-resource frontier | 15 | 9 | 0 | 51 | 24 |
| Canonical frontier + status lookup | 15 | 12 | 0 | 54 | 24 |

An **exact complete workflow** requires controller-visible completion of all four operations and four independently correct effects. The release-only arm reports all four acknowledgements in nine cases, but all nine contain a stale D result: acknowledgement completeness is not semantic correctness. Name-only matching fails in all three alias cases despite correctly guarding a direct-name dependency.

Global waiting and the canonical frontier both finish the three ordinary, three alias and three opaque cases correctly. In the three lost-ack cases, global waiting observes no progress, while the frontier completes and acknowledges B/C without pretending A is resolved. Status lookup then completes all four tasks in all three lost-ack cases. This costs one extra query input per lost-ack case.

In all three dropped-request cases, the lookup candidate completes only B/C and leaves A/D unresolved. Its five queries per case are wasted observations in this controlled condition, not a free benefit. Across all 15 lookup-arm cases there are **18 additional status-query inputs**. There are no mutating retries. The correct disposition for absence remains UNKNOWN.

Unknown footprints prevent pre-A overlap: all canonical opaque cases do zero B/C work before A resolves. This is a required conservative boundary, not a scheduler failure to be silently relaxed.

## Matched timing, at equal output correctness

The frozen performance gate uses **only six pairs**: three ordinary-delay and three alias cases. Both global and canonical arms produce the same four exact results in each pair.

| Metric | Median | Range | Matched observations |
|---|---:|---:|---:|
| Global workflow duration | 467.778 ms | 467.602--469.365 ms | 6 |
| Canonical frontier duration | 263.866 ms | 263.123--265.130 ms | 6 |
| Within-pair reduction | 204.276 ms | 203.826--205.037 ms | 6 |
| Within-pair candidate/global ratio | 0.563503 | 0.562577--0.564869 | 6 |

The median paired ratio corresponds to a **43.650% reduction in this constructed workflow**, passing the preregistered at-most-0.8 ratio. The deliberately injected 100 ms B/C waits are overlapped with the deliberately injected A wait. This is a mechanism calibration, not evidence of a 43.65% improvement in real agents, games, model calls, or arbitrary applications. It does not isolate CPU instructions, network time, human response or filesystem speed. Fixed order and three repetitions per cell do not justify a population confidence interval.

## Conditional noninterference argument

This argument concerns logical task resources and result values, not identical UI pixels or timing. The fixture's incidental status label can differ by schedule; policy never uses it for target selection or effect decisions. Real application focus, selection, clipboard, shared dialogs and hidden state would need to be included when they can affect task results.

| Symbol / field | Meaning and definition | SI unit / representation | Domain / assumptions | Type |
|---|---|---|---|---|
| p, c | A pending operation and a proposed candidate | 1 | Deterministic semantic operations with complete declared effects | Scalar operation identifiers |
| R_p, R_c | Canonical resources read by p or c | 1 | Finite sets, complete for relevant semantic state | Sets of identifiers |
| W_p, W_c | Canonical resources written by p or c | 1 | Finite sets, complete for relevant semantic state | Sets of identifiers |
| x | Logical application state before either operation | Resource-dependent values; no common SI dimension | Mapping over canonical resources | State vector / mapping |
| T_p, T_c | Semantic state transformers of p and c | Same state units in/out | Read only their R set, write only their W set; no undeclared influence | Functions |
| epoch, catalogue_version | Context and resource-map revision | 1 | Immutable for one advice/admission; changed values invalidate it | String / integer scalars |
| t_start, t_end | Measured policy-loop start and end | s, stored in integer ns | Same host monotonic clock, ordered | Integer scalar timestamps |

The sufficient scheduling condition is

\[
W_p\cap(R_c\cup W_c)=\varnothing,\qquad
W_c\cap(R_p\cup W_p)=\varnothing.
\]

First, p cannot change any value c reads, so c computes the same outputs whether it executes before or after p. Second, c cannot change any value p reads, so p likewise computes the same outputs. Third, their write sets are disjoint, so neither overwrites the other's result. Every untouched resource keeps its original value. Therefore, under these stated assumptions,

\[
T_c(T_p(x))=T_p(T_c(x)).
\]

For multiple pending operations, require the condition for the candidate against each pending operation. Move the candidate through the pending sequence one adjacent commuting swap at a time; each swap preserves logical outputs, so the resulting reordering preserves them as well. This does not prove liveness, decide whether an unacknowledged operation committed, or make an incomplete footprint sound. The status-lookup extension adds information under a separate application contract; it is not deduced from noninterference.

The finite test enumerates all **4,096** read/write-set pairs over three resources, compares the predicate to an independent set expression, and verifies two execution orders for admitted pairs on one deterministic state-transformer family. This is regression evidence, not a substitute for the conditional argument or a proof that arbitrary GUI footprints are complete.

Unit check: timestamp subtraction remains nanoseconds; division by 1,000,000 yields milliseconds. Resource-set predicates and time ratios are dimensionless. The 204.276 ms paired median is not obtained by silently subtracting unrelated clock origins. The median of the paired differences need not equal the difference of the two marginal medians.

## Tests, retained failures, and audit limitations

Before freezing: **30 gate/receipt tests + 9 audit mutation tests = 39 PASS**. The latter reject physical-release corruption, inverted acquisition times, a false completion flag, inconsistent database/document results, foreign accepted receipts, fabricated pending sets and advice claiming input authority. The same 39 tests pass after all 75 cases.

Construction smoke-01 failed because the installed python-xlib Display is not a context manager, before any GUI case. Smoke-02 executed one correct GUI workflow but the auditor incorrectly used Counter(dict), comparing timestamp values instead of key occurrences. Both exact source snapshots and failures are retained. These were repaired before freeze; smoke-03 then passed six development cases. None is pooled with the measured allocation.

An attempted container streaming invocation was unsupported and did not start a process or create the measured output path. The path/process absence was checked before the ordinary synchronous invocation. This did not consume or retry a case. Each of the three measured block directories was created once.

`replay.py` independently reopens all 75 databases, reruns the gate-independent auditor, verifies the frozen source hashes, schedule and block plan, and recomputes the tables. The raw append logs are trusted retained evidence, not an OS security boundary against a same-user process forging every file. X11 samples prove sampled key states, not continuous physical-state observation. Application receipts/aliases are trusted structured fixture capabilities, not facts inferred from screen appearance.

## H / T / D / C / U

**H:** dependency-scoped continuation can advance unrelated exact work during unresolved effects while protecting dependent reads; canonical identities matter; a bounded trusted read-only status lookup can resolve lost acknowledgement without replaying the effect.

**T:** the 75 fixed cases in three immutable blocks, 39 regressions including 4,096 finite effect pairs, complete SQL/trace replay, and explicit negative controls. Stop on first unexpected audit failure; no consumed block is rerun.

**D:** all six frozen gates PASS at the fixture scope. Canonical exact complete: 9/15; lookup exact complete: 12/15. Zero candidate premature reads. Dropped requests remain unresolved. Production-runtime integration, automatically inferred footprints and gameplay efficacy remain UNPROVEN.

**C:** a hidden common resource, stale alias catalogue, a status response for the wrong context or payload, a false commit receipt, or a GUI whose incidental state affects input can defeat the assumptions. A status lookup may itself be costly or lack a reliable capability. Sequential-only applications can eliminate the overlap benefit.

**U:** engineered delays, hand-authored complete logical resources, trusted structured feedback, one fixture, fixed rotation rather than full counterbalance, shared-host scheduling and small per-cell sample size dominate. No calibrated combined standard uncertainty or coverage factor is available; no population success probability is inferred.

## Reproduction and retention

The evidence bundle contains all sources, the exact local plan, the development failures, 75 real databases and input/receipt/application logs. `archive.json` on GitHub pins its bytes and SHA-256. Extract the bundle and run:

```sh
cd research/cross_domain/pending_effect_frontier_v1
python -m unittest test_frontier test_audit
python replay.py
```

These commands replay retained evidence and do not create GUI input. A new live run requires a distinct allocation ID and newly frozen plan; never reuse the three consumed output paths. The 30 gate tests alone need no retained GUI fixture. The nine audit tests need the included development smoke fixture.

## Primary sources and cross-domain transfer

- Bocchino, Adve, Adve and Snir, *Parallel Programming Must Be Deterministic by Default*, HotPar 2009, especially effect systems and aliasing: https://www.usenix.org/legacy/event/hotpar09/tech/full_papers/bocchino/bocchino_html/paper.html . The present experiment does not inherit that paper's language guarantees.
- University of Illinois, *Deterministic Parallel Java Tutorial*, noninterference contract: https://dpj.cs.illinois.edu/DPJ/Download_files/DPJTutorial.html . This is background for resource-conflict reasoning, not evidence about our measured GUI.
- SQLite, *Isolation In SQLite*: https://sqlite.org/isolation.html . Our read-only lookup is implemented by the application after its local transaction commits; it is not a general remote-system guarantee.

Related fields: **programming languages/compilers** (effect sets and alias identity), **distributed systems** (uncertain completion and read-only reconciliation), **control/HCI** (serialized physical input with overlapping application work), and **measurement science** (independent semantic outcomes versus acknowledgements).

The next high-information integration is a real multi-document application with runtime-issued, freshness-bound resource handles and a user-visible status capability. Do not introduce this scheduler into continuous Doom movement merely because the GUI calibration passed.
