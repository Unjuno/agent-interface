# Primary V2 review rescue

Source `9720dd3197ff5c7dba4b322de5d614f61c6d0bdc` on `review/current-primary-v2-45e9-20261003`. Preserve both original first-error author packet and V2 review byte-for-byte. Prior V1 packet already matches main and is not rewritten. No obsolete production/workflow changes are restored.

Original review distinguishes author RED2/GREEN41, three controlled decoder first-error cases, ten copied refusals, composed56 first54pass/2fail due missing startup directory, then environment-only repair56pass. Original failures, first export/audit errors, projected private custody limits and unchanged V1 FAIL/HOLD remain intact. This rescue transfers no old adoption votes or future-main certificate.

The original two failure-order tests run against current main without changes and pass2/2. Therefore no production repair is introduced: current implementation already preserves the first busy diagnosis in these two directed cases. Original test definitions are restored for explicit selection; they require a fresh `PRIMARY_FAILURE_EVIDENCE` directory and are not added to default CI discovery. This is not the historical decoder composition or Windows runtime replay.

`verify_saved.py` validates public manifest bytes only with explicit guards. It does not run original archived producers/auditors, authenticate missing projected private originals, certify physical release/backend/task benefit or close the broader goal.
