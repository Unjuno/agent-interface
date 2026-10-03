# Qualified actual-asyncio trace — retained-data audit v2

**PASS_RETAINED_TRACE_V2_SCOPED**: the unchanged 48-row / 120-outcome raw has
zero v2 errors. V1 accepts all seven reviewer contradictions; v2 rejects all
25 effective controls (seven reviewer, eight original-boundary and ten adjacent
controls). See [control decisions](execution/controls.json), [v2 CLI result](execution/audit-v2.json)
and [actual command/UTC/exit receipts](execution/receipts.json). All six regression
methods pass. The original 27 manifest hashes still match. Native macOS
CPython 3.14.5 retained-data checks, source-frozen audit/test/mutation definitions;
the separately added characterizer is included and hashes itself in the result.

This is the current entry for PR #6890. The [original first run](../README.md),
[raw](../execution/raw.json), [frozen source](../FREEZE.json), v1 auditor and its
first result are preserved unchanged. A nonauthor review found seven contradictions
that v1 accepts; those findings qualify its audit completeness, not the measured
contrast in the unchanged raw. [The repair plan](PLAN.md) fixes the added gate.

The standalone [v2 reducer](audit_v2.py) joins producer/waiter payload and generation,
reduces remaining from unique ordered detach events, requires one producer terminal
before its exit, binds error identity, and reconciles terminal cancellation with
the before/after task snapshots. It also validates exact JSON scalar types,
complete offered conditions, event roles, barriers and cleanup causes.

The seven findings and nonauthor focused reconstruction were supplied by distinct
worker `01a0ff2d-eb8e-70e0-82bb-ba3bf0c79b5c` in [review](https://github.com/Unjuno/agent-interface/pull/6890#issuecomment-5964335802)
and [supplement](https://github.com/Unjuno/agent-interface/pull/6890#issuecomment-5964353535).
This authored implementation and regression suite do not replace renewed review.

No candidate/asyncio matrix is imported or rerun. v2 operates on retained data only.
The exact raw hash must be supplied to its CLI; copied-control tests exercise
internal consistency separately from that byte gate. Dynamic joins, arbitrary
schedulers, truthful log emission, coordinated fabrication, duplicate-member JSON
parsing policy, GUI/task effects and efficiency remain unverified. Duplicate-member
JSON is outside the parsed-object contract; exact original bytes are separately pinned.

From this directory, ordinary regression checks are:

```sh
python3 -B -m unittest -v test_audit_v2
python3 -B audit_v2.py ../execution/raw.json \
  --expected-raw-sha256 d3262358814f4fd724d0b36b0fc027d2b4fee70f5a7e56a090d8ee794c5c2441 \
  --output NEW_AUDIT_OUTPUT.json
```

The output must be new; do not overwrite first results. Original `../SHA256SUMS`
still resolves every original file, including its historical README. v2 adds a
separate source freeze, execution records and manifest; no original hash is updated.

Local index reaches 156 top-level studies and public navigation checks 26 documents /
1,631 relative links. These are retained in execution receipts; optional hosted CI
is not claimed passed. The original guest remains stopped; no new guest/container,
candidate, shared input/model/GPU or runtime invocation was needed. V1's eight
successful controls are historical and do not establish full event audit coverage.
Renewed FINAL-v5 nonauthor content quorum/current-base combination/application
remain pending for the new head; the original proposal is held, not reused.
