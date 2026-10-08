# T6 — total delivery-position loss identifiability

**H:** A row-only adapter cannot distinguish a current stream with `release_batch_delivery_position` deleted from all release rows from a valid legacy-shaped stream when both carry the same `input-release-batch-v3` marker.

**T:** Compare one valid two-member current-format stream (delivery positions 0,1), its all-fields-deleted form, and the identical legacy-shaped input using the frozen T5 adapter. Source: current `main` `2a9052efdd155b8cdc173d216a969ea5f64a1ce9`; backend blob `193c2bd231795e7ee57de64aedfd741c8b814013`; adapter SHA-256 `6f0ad1eb378b8269d596b6d7f38ec21c3e447c7f41814b974f6aa19a7250b58c`.

**D:** If total-loss rows equal legacy rows on adapter inputs and both yield `SOURCE_ROWS_JOINED / TEMPORALLY_UNIQUE`, report `UNIDENTIFIABLE_WITH_ROW_FIELDS_ONLY`; this is a representational limit, not proof of live corruption. Otherwise identify the row-level discriminator.

**C:** Session-level provenance or a distinct schema version could disambiguate. The probe intentionally limits the adapter to row fields.

**U:** Synthetic adapter construction only. No live runtime, GUI, OS input, game, model, causal attribution, task effect, safety, recovery, latency, or completion claim.

## Result

Current `main` source emits `release_batch_delivery_position`, but its release rows retain the same V3 schema marker used by the older contract. Deleting the field from every release row makes the current-shaped rows identical to the legacy-shaped rows accepted by T5. Both yield `SOURCE_ROWS_JOINED / TEMPORALLY_UNIQUE`, with causal attribution still `NOT_ESTABLISHED`. T5's mixed-subset case remains distinguishable and fail-closed; total loss is not distinguishable from legacy using the row-only interface.

## Reproduction

From this directory:

```powershell
python -B -m unittest discover -s ..\package -p test_*.py -v
python -B -O -m unittest discover -s ..\package -p test_*.py -v
python -B probe.py
python -B audit.py
```

