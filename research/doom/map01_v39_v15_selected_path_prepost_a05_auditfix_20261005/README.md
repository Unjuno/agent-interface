# A05 — corrected A04 hash binding

A05 is a distinct audit allocation, not a retry of A04. It fixed the undefined PRE-RUN variable and ran once against the unchanged A02/A03 evidence. Input hashes matched and all 12 mutation controls were rejected, but its baseline expected an empty normal-case pre-sample where the retained query and result both contain `[65, 74]`. See `RUN_RECORD.md` and `DISPOSITION.json`. Candidate invocations: 0; auditor invocations: 1; retries: 0. A05 is terminal and must not be retried.
