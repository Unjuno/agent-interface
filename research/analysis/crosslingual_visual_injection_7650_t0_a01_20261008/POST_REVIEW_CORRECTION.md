# Post-review qualification — A01 auditor row-binding gap

Added 2026-10-08 after independent review of the immutable A01 run.

The A01 auditor verified the set of IDs and aggregate language/class cell counts, but did not verify that each row's language/class/family/variant fields matched the components encoded in that row's ID. A coordinated reassignment of metadata between rows could preserve the ID set and aggregate counts and pass A01. Preserve the original A01 `PASS_MACHINE_GATE_SCOPED` output, candidate, audit output and hashes unchanged as the historical recorded outcome; however, that outcome does **not** establish complete row-to-ID ledger reconstruction and is insufficient for that stronger claim. A02 separately audits this residual on the same immutable raw bytes.

Independent review also noted that the A01 protocol's phrase “English semantic-frame IDs” can imply that linguistic stimuli exist. They do not: these are metadata-only family IDs and every text field is a placeholder. This clarification does not edit the frozen A01 protocol. The additive A02 successor supplies a corrected read-only auditor over the exact A01 raw bytes; it does not rerun or replace A01.

The A02 gate can establish row/ID metadata consistency in this synthetic artifact only. It cannot establish semantic translation equivalence, actual screenshot pixels, visual legibility, or model behavior. Issue #7650 full T0 remains HOLD.
