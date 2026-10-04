# T3 first outcome — STOP_AUDIT_MUTATION_SENSITIVITY

Candidate ran once/exit 0; auditor ran once/exit 1; retries=0. Auditor identified both malformed-order rows as `FAIL_TIMESTAMP_ORDER_NEGATIVE_ACCEPTED` separately from integrity, but its one-row classification mutation left the aggregate FAIL unchanged; only 3/4 mutations were distinguished. This is not a qualified result. Do not rerun T3. Preserve raw and first auditor output under [output/](output/) and see [STOP.md](STOP.md).
