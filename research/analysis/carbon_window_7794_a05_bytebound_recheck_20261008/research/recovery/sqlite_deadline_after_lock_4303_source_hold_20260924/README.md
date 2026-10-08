# SQLite deadline after lock wait — #4303

Allocation `sqlite-deadline-after-lock-4303-20260924-01`.

H: an initially timely semantic proposal can expire during SQLite's own busy wait. Compare PRE_WAIT_ONLY and POST_WAIT_RECHECK while preserving the same write transaction and current target/generation check.

T: actual independent lock-holder/publisher processes and private SQLite WAL databases, CPython standard library. FREE, SHORT, EXPIRES_WAIT, PRE_EXPIRED, BUSY, CHANGED; two policies; three repetitions; four immutable nine-case batches, each once. No GUI/model/provider/OS task input/network experiment.

D: candidate late INSERT receipts 0; weak expired-wait late INSERT receipts 3; both retain timely FREE/SHORT and refuse expired/changed/BUSY cases; complete raw DB/process/IPC/source reconstruction and all12 effective mutation tests. Missing evidence, failed exposure or a no-op mutation is HOLD/STOP. Candidate late insertion or wrong binding is FAIL.

C/U: directed cooperative fixture, complete authored dependencies and same-host monotonic clock. INSERT-time receipt is not durable commit or application-effect time. A post-wait check cannot guarantee a hard commit deadline against later preemption/I/O. No production, task, token, speed or reliability-frequency claim.

The lossless SOURCE capsule includes the full PLAN with variable/unit table, exact schedule, environment, schema, actors, supervisor and independent auditor/controls. SOURCE.json binds all files and parts by SHA-256. The full source is published before the formal allocation. No old study is rerun or pooled.

Restore to NEW directories (from this directory):

```
python -B restore.py SOURCE restored/science
python -B restore.py EVIDENCE restored/evidence
python -B restored/science/audit.py restored/evidence/formal
```

The latter two commands apply after the evidence capsule is published. Revalidation reads retained DBs only; do not invoke run.py on a consumed allocation. First outcomes and construction incidents are preserved separately. An overall result requires both the raw gate and all12 controls.

SQLite API rationale: https://sqlite.org/c3ref/busy_timeout.html and https://sqlite.org/lang_transaction.html . These explain the mechanism, not the outcome of this allocation.
