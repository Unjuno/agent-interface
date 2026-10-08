# A03 saved-source audit

## Lineage and scope

This is an additive, read-only audit of the immutable #4193 `RAW_USED.json.xz` corpus. It does not read, repair, replace, or treat v3's malformed `RESULT.json` as the oracle. It does not rerun the old candidate, old auditor, game, or any consumed allocation.

Freeze commit: `84be79757c8bc18eea1ecaf5edb8f392e3e6e425`.

## H / T / D / C / U

**H.** Independently parsing the exact retained compressed source will reconstruct six session streams, 194 typed scorer observations, and three identity-consistent physical DOWN/UP joins, while confirming zero observed kill/map-exit endpoint transitions and no producer `source_event_id` or `scorer_event_id` fields.

**T.** Read the exact raw blob from its canonical repository path and verify SHA-256 `0d55f782f0e129738b422e52d8066f7fb69a02ebcf2c1691ee711e74a369a740`. Parse each element of the per-session JSONL string arrays independently. Check exact session/sample inventories, exact integer/bool field types, monotone scorer timestamps within each session, recursive event-ID absence, attack physical bracket/adapter identities, and absence of input events from no-input sessions. Run the separate mutation tests once.

**D.** `PASS_READ_ONLY_SAVED_SOURCE` only if all frozen inventories and physical identity joins agree, all six scorer streams have strict within-session order, and both attack and no-input streams contain zero positive endpoints. Any raw hash, schema, identity, type, order, or endpoint discrepancy fails the audit.

**C.** The event source stores JSONL records as arrays of JSON strings inside the outer JSON object. The auditor explicitly decodes those strings before checking nested keys; it does not rely on recursive traversal of the undecoded outer object. `sample_ns` is compared only within its own session.

**U.** This is retained-source corroboration only. It does not establish scorer truth, a positive task effect, causal attribution, application consumption, multi-actuation coverage, live control, recovery, or MAP01 completion. The published v3 `RESULT.json` remains malformed and untouched; this package is not a corrected v3 result.

## Command

From the repository root:

```sh
python3 -B research/doom/map01_task_effect_receipt_boundary_4193_successor_v1/a03_saved_source_audit_20261005/audit.py
python3 -B -m unittest -v research.doom.map01_task_effect_receipt_boundary_4193_successor_v1.a03_saved_source_audit_20261005.test_audit
```

The first command reads only the hash-pinned retained raw and writes this package's new `results/AUDIT.json`; it never writes to v3. The test command uses in-memory mutations only.
