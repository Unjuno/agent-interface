# Source-first freeze — grantor-side capability revocation v1

Task `COORD-GRANTOR-CAP-REVOCATION-20260917-026`, Issue #620.
Publication BASE `46cbcadabdfe8685f52353f455264568ebf3b2e7`.
Formal allocation `grantor-cap-revocation-20260917-a1`.

Before each exec the helper deliberately duplicates the original capability to an inheritable alias and marks only the original non-inheritable. The single intervention is grantor behavior at the helper-reported lifecycle boundary: `recipient_only` ACKs while keeping its endpoint live; `grantor_revoke` closes the server endpoint before ACK. Same helper/task PID, task decision, owner receipt path, DB isolation and atomic token-check+generation-commit are held fixed.

Formal schedule is exactly the 12 `m*` cases in `plan.json`, executed as six 2-case chunks. No measured-ID rerun/replacement/extension. Excluded construction uses only `c*` IDs.
