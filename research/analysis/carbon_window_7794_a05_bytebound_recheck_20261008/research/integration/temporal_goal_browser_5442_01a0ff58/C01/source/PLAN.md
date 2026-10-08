# #5442 temporal goal / ordinary construction C01

Worker 01a0ff58-2d0b-7eb1-8b33-c8b69e63563a, FINAL-v5.
Scientific parent #5442; claim5965728887. Source base316ac44b24d4ac29c1942d2fee51f1c0599855b1.
Branch research/5442-temporal-goal-01a0ff58-20261003; additive evidence subtree research/integration/temporal_goal_browser_5442_01a0ff58.
This is a finite independent authored-app construction, not a T7/T8/6914 replay or production mechanism.

H: With identical authored exact-value goals, a cached APPLIED receipt proves a past transition, not a later goal state.
A fresh public UI observation plus standard version-conditional SQLite UPDATE and a two-new-attempt bound preserves
the goal through one finite read/write race, refuses stale writes, avoids a write after ABA restores the goal,
and yields without a false completion when interference persists. Goal satisfaction is point-in-time value/target
equality; continuous validity, attribution of an externally restored value, and irreversibility are separate.

T: First prove the finite state/guard predicates with ordinary private SQLite controls. After source freeze, start
one fresh dedicated loopback HTTPServer / SQLite database and one owned hidden IAB DOM-only tab. Ten distinct cases:
two authored Unicode strings times stable / overwrite / one read-write race / persistent read-write races / ABA restore.
Order is forward history order for string1, reverse for string2. Generic app reads only case IDs; it contains no history
branch or desired-goal classifier. Goal/controller uses public rendered state/receipt and forms; it receives no private
SQL observer output. Serialized disturbance requests run between read and submit; this is not a scheduler stress test.

Phases: initial10 exact guarded form edits; freeze fresh SQL snapshot/backup. Then disturbances: overwrite/one_race/
persistent_race get one competing value; ABA gets competing then goal value; stable untouched. Public fresh observations
follow. For each unsatisfied goal, open a fresh form. A one_race/persistent_race disturbance occurs after reading repair1
version and before submit; a persistent_race disturbance also occurs after reading repair2 and before submit. No other
disturbance, mutation or reset is allowed. A satisfied goal gets no repair write. At most two repair submits/case.
Every form identity/nonce is distinct and saved before submission; twenty task POSTs are expected, ten repairs in total.
The three SQLite snapshots and original empty SQLite bytes are retained; source/raw/first failures never replaced.

D before outcomes: expected initial10 APPLIED/current satisfied. After disturbance, four current satisfied (stable/ABA),
six unsatisfied despite all10 preserved historical APPLIED receipts. Repair10 yields four APPLIED and six CONFLICT;
final eight current satisfied/two persistent cases YIELD_BUDGET. Sibling B remains exact initial bytes/version0 everywhere.
PASS only if actual intended target/namespace/goal/nonce/version, complete journal/UI/source joins, three fresh snapshots,
zero false current-goal labels, max2 attempts and no ABA/stable repair agree with independent raw-only reconstruction.
Any wrong write/collateral mutation/false completion/extra attempt is FAIL and retained. Missing custody or unknown action
is HOLD/UNCERTAIN; no resend/reset. No primary source edit/restart or submit retry to obtain PASS. Construction fixes may
be versioned before freeze. Stop on any unknown browser action, source mismatch, server failure, unexpected side effect,
200 journal requests /20 task mutations /20 disturbances /12MiB output bound. Preserve partial data and clean only own tab/PID.

C: Scripted case order and serialized controlled disturbances; authored UI/SQLite authority; baseline deliberately applies
historical evidence to a current predicate and is not an implementation of current-state confirmation. Atomic conditional
UPDATE is a strong existing standard. No new transaction theory, superiority over a fresh-read baseline, or novel mediator.
Retained real Writer post-guard TOCTOU evidence (#282) is stronger for that native-app boundary and is not superseded.
This tests previously absent post-success changes and no-extra-write/finite-stop transfer on the owned IAB/SQLite route.

U: No arbitrary-app observer authenticity, coordinated-fabrication resistance, continuous postcondition, physical input
occupancy/release, concurrent-scheduler safety, crash/power-loss durability, latency/model/token/cost/efficiency benefit,
MAP01 completion or runtime adoption. No model/backend/container/GPU/native-pointer allocation. All goals/data are invented.
Independent observer backup is a new read-only process, not a proof that its authority is authenticated. HTTP200 is server
prepared-response journal plus actual delivery-accepted DOM; no separate client wire/header instrument is claimed.

Sources: SQLite conditional UPDATE affects only matching WHERE rows and zero matches is not itself a SQL error
(https://www.sqlite.org/lang_update.html); explicit transactions/one SQLite writer/snapshot semantics
(https://www.sqlite.org/lang_transaction.html). Saltzer/Reed/Clark end-to-end placement is the parent analogy
(https://web.mit.edu/saltzer/www/publications/endtoend/endtoend.pdf), not an agent/runtime result.
Both app and evidence source authored here; repository Apache2.0; no borrowed third-party implementation or new package install.
