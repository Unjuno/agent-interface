# Semantic proposal publication — Issue #4299

Successor to closed #4257. No old results or runtime files are changed.

## Prospective source/gate freeze

Allocation `semantic-publication-4299-20260924-01`; formal batch invocations so far: 0.

H: a check outside publication's transaction can become stale before INSERT; atomic read-set validation and publication should exclude that gap.
T: actual SQLite worker/writer subprocesses; CHECK_THEN_PUBLISH vs ATOMIC_VALIDATE_PUBLISH; eight schedules, two repetitions, 32 cases, four immutable eight-case batches. DELETE journal, synchronous FULL, busy_timeout=0. Trigger journal reconstructs publication-state bindings. Complete authored dependencies only.
D: candidate stale publications0; weak target/ABA stale publications4; all32 case/64 child process receipts; expected refusal/BUSY/mutation preservation; separate raw audit and all12 effective corruption controls. No rerun/replacement/tuning. Any missing evidence or no-op control is HOLD/STOP, not PASS.
C: SQLite serializes unrelated writers too. This is a known transaction mechanism applied to a semantic-evidence boundary, not novel database research.
U: no GUI/model/task authority, latency/token benefit, crash/power-loss durability, arbitrary dependency discovery or production claim.

Full PLAN, variable/field table, exact sources, schema, schedule, environment and source hashes are in the lossless SOURCE capsule. Construction: four excluded real-process cases; raw-only audit229 checks/errors0; 12/12 effective mutations rejected. Construction raw will also be retained in the complete evidence capsule.

```sh
python -I -S -B unpack.py SOURCE_MANIFEST.json /tmp/semantic-4299-source
```

This restores only data; it never runs an experiment. Source archive SHA-256 `d90d4fff7b2f45c8160cadb737914639cf46d0fb38e5dc9ef5145f901468c241`; FREEZE SHA-256 `eb494ef033f94a1a22076c856704a2ebf82c72f8af30bae2823b11c131036ba2`.

Primary semantics: https://sqlite.org/isolation.html and https://sqlite.org/lang_transaction.html . Publication validity is at the transaction boundary, not a promise of future currentness or action authority.
