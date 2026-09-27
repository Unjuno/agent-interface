# Conditional proof and counterexample

Variables, units and definitions are in PLAN.md. All equalities below compare
like-typed dimensionless integers or strings. This is a restricted correctness
argument, not a new theorem about arbitrary database instrumentation.

## Restricted statement
Assume: q reads exactly one resource r in a,b,u; schema identity fixes that
resource; preparation reads value and version in the same SQLite snapshot;
every change of a value increments its version atomically; versions do not wrap
or reset in the examined lifetime; D contains r; validation and private effect
publication share one serialized write transaction; there is no other source
of the computation.

The check is:

    s_p = s_c and, for every resource r in D, v_p(r) = v_c(r).

1. Equal schema cookies under the stated cooperative lifecycle retain the
   binding of q to r. This is an assumption about this fixed schema protocol,
   not arbitrary restored/copied databases.
2. The preparation snapshot binds x_p to v_p(r).
3. Any intervening change to x_p would increment r's version. Versions cannot
   reset, so equality v_p(r)=v_c(r) rules out such a change. Thus x_p=x_c.
4. BEGIN IMMEDIATE prevents a cooperative writer from changing r between that
   successful version check and publication of the private effect.
5. Therefore publishing x_p cannot be a stale-value effect in this model.

Metadata reuse does not reuse v_p: a fresh version is queried in the same read
transaction each time. The proof therefore does not require recompiling q on
every execution. It DOES require the metadata still contain r. Empty metadata
is UNKNOWN for the candidate, never proof of independence.

## EVENT_ONLY counterexample
1. The cold q on table a compiles and emits a SQLITE_READ callback.
2. Reset the event list but retain the connection's prepared-statement cache.
3. The warm q executes and returns current a0; no compilation callback is emitted.
4. Treating this absence as D empty omits a's revision.
5. A separate cooperative writer atomically changes a0 to a0+changed and raises
   revision1 to2 after preparation.
6. Schema equality still holds and the empty all-revisions check succeeds.
7. The private effects table stores old a0. A separate read-only database query
   observes both the changed source and the old effect.

This is a misuse of an observed compile-time signal as a dynamic execution
record, not a SQLite authorizer bypass or production security claim. All SQL
and callbacks in this experiment are authorized and fixed.

## Precision qualification
For a singleton r, rejecting a change only to unrelated u is unnecessary.
Complete, exact D={r} avoids it. However compile callbacks can overapproximate
actual evaluation. Construction found both old a and new b during a view
retarget in NO_STATEMENT_CACHE. Checking this superset stays conservative but
may refuse because old a changed. No general minimality proof is made for the
candidate; its precision claim is limited to the declared finite corpus.

## ERROR CHECK
The argument needs complete dependencies, non-resetting versions, coherent
preparation and atomic check/publication; removing any is outside its theorem.
It proves no historical truth, authentication, latest-at-response claim,
exactly-once distributed effect or GUI safety. Dimensions are consistent;
counts and revision comparisons are dimensionless, timestamps diagnostic only.

## Primary documentation
SQLite compile-time callback timing and schema-triggered repreparation:
https://sqlite.org/c3ref/set_authorizer.html
Python3.13 sqlite3 connection statement-cache and callback interfaces:
https://docs.python.org/3.13/library/sqlite3.html
SQLite explicit transactions and BEGIN IMMEDIATE:
https://sqlite.org/lang_transaction.html
