# Effect observation cannot precede its recorded execution start

The typed mechanical API previously accepted a matching `EffectReceipt` whose
observation time was earlier than its accepted `ExecutionReceipt.started_ns`.
For example, accepted begin400, recorded start600 and effect observation599
could advance an executed lifecycle to VERIFIED. This is an internal temporal
inconsistency under the declared comparable-clock contract. A two-line guard
now rejects that observation before assigning effect or terminal stage.

The selected production base is316ac44b24d4ac29c1942d2fee51f1c0599855b1.
The earlier source freeze separately observed main816724f93a7239b3ad9b5ebb2e5f79b8a103b2db;
the prospective C01 freeze observed main9c26e204c0475bee30919e3d0e6681f393078ef1.
A read-only Git comparison found kernel/core and the kernel workflow unchanged
between selected base and9c26e2. This does not certify any future merge tuple.

The first ordinary baseline ran six literal methods on an unmodified fresh
checkout and exited1 with eleven expected assertion failures, zero test errors.
Its original complete captured streams and actual command/times are retained.
However, an earlier freeze helper wrongly expected9 rather than10 kernel
entries and failed. The baseline was mistakenly invoked after that failed
dependency. Original source/test/plan expectations preceded execution, but their
byte hashes and exact working/Git snapshots were recorded afterward. This
baseline has post-run identity evidence, not a successful prospective hash
freeze. It has not been rerun or replaced. [SETUP_NOTES.md](SETUP_NOTES.md) also
preserves the interrupted sparse setup, owned lock custody and first guard
refusals; early tool errors have no separately captured UTC/full-stream files.

The corrected TDD freeze succeeded before modifying production or running green
checks. All25 retained inputs remain exact. The six active tests cover every
effect status before start, refusal custody and valid recovery, recorded start
rather than the earlier accepted begin, equality, during-execution/late delivery,
and wrong command/manifest. Focused6, kernel49 normal and kernel49 optimized
methods each passed. The whole kernel uses the existing local/CI entry:

```text
python -B -m unittest discover -s runtime/kernel -p 'test_*.py' -v
python -B -O -m unittest discover -s runtime/kernel -p 'test_*.py' -v
```

C01 is a separately prospective ordinary construction comparison. Its35-input
freeze pins the complete original inputs, candidate four-file snapshots,
fixture, matrix, raw-only auditor and declarations before execution. Two arms,
three statuses, ten timestamps and three identities produce180 complete rows.
Both source arms run the same typed sequential fixture in separate private
namespaces; no current runtime import or external backend is used.

| Complete90-row arm | Matching accepted | Pre-start matching accepted | Identity mismatch refused |
|---|---:|---:|---:|
| Unchanged selected source | 30 | 12 | 60 |
| Two-line candidate | 18 | 0 | 60 |

The separate stdlib auditor imports no matrix or kernel and invokes no source
producer. It checks the ordered full census, exact type-sensitive attempted
receipts, complete before/after state and terminal outcome against a literal
oracle. All8 effective copied-raw corruptions refuse, including boolean/float
aliases, changed admission, execution lost on refusal, false effect truth,
missing row, changed source identity and extra state. Original raw is unchanged.
Matrix UTC05:13:15.433002–05:13:15.636488 and auditor05:13:16.430635–05:13:16.724627,
both2026-10-03, exit0, one invocation each, no retry. Raw SHA256
83133cc2bae937daf479567391d475a27d3c067e828010a9ce293154555b60b0;
freeze SHA256d89471361063d08bea9dbfecbc16edb7bcfb0da5f2a05a3373312b6c5c2c9580.

Captured originals are held privately without modification. Published capture
receipts replace the private task-root/interpreter paths with explicit markers;
stderr changes only the exact task-root prefix. Other streams remain exact.
CAPTURES.json identifies each original and public byte length/hash plus the
transformation; it does not claim that a projected receipt preserves lexical
JSON bytes or authenticates inaccessible private originals. Source snapshots,
primary raw and audit themselves remain exact published bytes.

Host checks use CPython3.12.10 on Windows/AMD64, one child at a time, stdlib only,
30s timeout and2MiB per captured stream. No formal/live allocation was consumed
or replayed, and no backend, GUI/input, model/provider, container/WSLc/GPU or
shared resource/apply lock was used. No cross-platform CI execution is asserted.

This adopts only the necessary recorded-start lower bound. It is sufficient for
this typed synthetic inconsistency and does not prove truthful clocks, ordering
after the last action, terminal physical release, task effect or efficiency.
A truthful monotonic caller may already satisfy the relation. Nominal non-record
admission and cancellation occurrence semantics remain separate source-owner
units. Historical #5216/#5225/#5229 raw/first outcomes/HOLD are untouched. Full
computer control remains unresolved; runtime promotion still requires its own
genuine nonauthor content votes and actual-current combination/apply evidence.
