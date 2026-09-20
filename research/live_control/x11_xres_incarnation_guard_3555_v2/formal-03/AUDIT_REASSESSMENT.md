# Post-run audit reclassification

Allocation `issue3575-xres-guard-formal-03` is retained unchanged. The candidate runner queried both `pixels_p1` and `pixels_p2` after p2 had acquired the recycled XID, so both reads addressed p2's same current window. The raw-only and supplemental auditors verified byte equality of those two reads but did not establish p1's pre-exit bytes. Therefore the issue's exact-pixel-reuse precondition is unproven for this allocation.

Reclassified outcome: `HOLD_AUDIT` (not an observed guard failure). The original raw, candidate PASS label, audit JSONs and hashes remain intact as historical evidence of the audit gap. Formal-04 captures p1 pixels while p1 is alive, before p1 exits, then independently compares them with p2 after reuse.
