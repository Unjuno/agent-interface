# Raw ledger retention boundary

The #1250 first-outcome raw ledger is 62287906 bytes / 20,000 JSONL rows with SHA-256 `53eb15adb992fc834815af55a338d1aaf626c1bb7d98b3c68737bc162b1f59d8`.

It is not copied into Git in this retention step because it is ~62.3 MB of high-volume per-receipt evidence and the repository is already artifact-heavy. Git retains exact compact result/audit/corruption/report artifacts plus the source-first bundle and full ledger digest. Consequently the complete per-receipt replay still requires the local raw ledger; scope the PASS accordingly.
