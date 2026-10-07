# Read-only observer lifetime and SQLite commit: bounded #6526 construction

This is a manually invoked, native Windows SQLite mechanism study. It asks
whether a read-only verifier can change persistence of an otherwise identical
writer operation, rather than merely report a stale value. It is ordinary
construction in private files, not a rerun, repair or replacement of #6526's
consumed GUI A01/A02/A03 allocations. No app, browser, physical input, container,
model or game is opened. No production runtime or mandatory verification is changed.

The primary SQLite references already explain rollback-journal read locks and
COMMIT returning SQLITE_BUSY while another connection has a read transaction:
[transaction control](https://www.sqlite.org/lang_transaction.html),
[locking](https://www.sqlite.org/lockingv3.html), and
[isolation](https://www.sqlite.org/isolation.html). This study transfers that known
mechanism to observer-intervention accounting; it does not claim a new SQLite
result or diagnose an existing production application. SQLite is public domain:
[license](https://www.sqlite.org/copyright.html).

H: In this frozen small DB, holding a target read transaction during an unchanged
writer UPDATE/COMMIT can prevent persistence under DELETE with busy_timeout=0;
the short-lived reader and pager-independent SELECT 1 control should not. WAL
should permit the writer to commit while the held target reader still reports
its old snapshot. Such a verifier can be SQL read-only and still intervene.

T: Sixteen distinct new databases, fixed source order: two journal modes, four
observer lifetimes, two desired strings. All cursors finish explicitly. The
actor executes BEGIN IMMEDIATE, one UPDATE, a private-state SELECT and one
COMMIT, with no retry. On SQLITE_BUSY it rolls back rather than silently changing
policy. All actor connections close before a separate-process mode=ro scorer
reads the persisted task row. Actual native SQL traces, error codes, transaction
state, changed-row counts, connection-close order, process exits/UTC and closed
DB hashes are retained. The observer uses both URI mode=ro and query_only=ON.

D: The exact predeclared matrix and eight effective copied-raw negative controls
must reconcile with separate raw-only logic and native DB witness reads. An
unexpected journal, exception, endpoint or count remains FAIL/STOP and is not
rerun. The producer and original retained-data audit each have one invocation;
ordinary construction fixes before freeze do not consume a GUI allocation.
Successful audit establishes this finite mechanism only, not #6526 H_PASS.

C: A held BEGIN/SELECT 1 is a negative control for transaction lifetime without
target-pager access. Short SELECT control separates observer presence from lock
lifetime. Mode=ro mutation rejection is tested separately before freeze. WAL's
old snapshot is a distinct freshness issue already studied in #4063; #4299 uses
a competing writer and #4303 a write-lock wait, not this intervention contrast.
No deadline, natural app polling behavior, fairness or timing inference is made.

U: One Windows/CPython/SQLite build, one tiny schema, two fixed payloads,
single-thread deterministic actor ordering, separate SQLite connections and a
fresh scorer process. No GUI task generalization, performance gain, prevalence,
physical resource independence or reader-process equivalence is established.
Ending a probe promptly can avoid this constructed lock; actual applications
still require appropriate task-effect verification. Do not weaken their checks
or set production WAL merely to make these cases pass.

Reproduce in a fresh writable private directory using the frozen sources:
`python invoke.py construction -- python construction_check.py`, then
`python freeze.py`; publish/record that new prospective source before invoking
`python invoke.py producer -- python assay.py --freeze freeze.json --out first`
and `python invoke.py audit -- python audit.py --freeze freeze.json --out first`.
Do not invoke either against an already consumed original output. The checked-in
closed DB witnesses use base64 for lossless text transport; decode into a new
private `first/dbs` directory before retained-data auditing. Outcome, provenance,
final manifest and actual publication commit are appended outside this frozen
README/source identity after execution.
