# Qualified actual-asyncio trace — retained-data audit v2

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
