# Raw ledger retention boundary

The first-outcome raw ledger is 61918949 bytes / 20,000 JSONL rows with SHA-256 `14318b345b35ae84e3e5203ff989ca81fa2f2e576cc747222f35384b3b68a438`.

It is intentionally not copied into Git in this retention step because it is ~61.9 MB of high-volume per-receipt transport evidence and the repository is already artifact-heavy. The compact `FORMAL_RESULT.json`, independent `AUDIT.json`, `CORRUPTION.json`, `RESULT.json`, and exact source freeze are retained. This boundary means the full independent receipt replay cannot be reproduced from Git alone; do not promote this failed allocation to a stronger claim.
