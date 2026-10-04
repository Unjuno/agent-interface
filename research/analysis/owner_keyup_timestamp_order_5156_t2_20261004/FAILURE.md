# T2 first outcome — STOP_AUDITOR_CLASSIFICATION_BUG

Candidate ran once/exit 0; auditor ran once/exit 1; retries=0. Raw contains `measurement_ready=true` for both novel malformed-order cases, but the frozen auditor put those scientific mismatches in its integrity-error list and stopped. It rejected 4/4 integrity mutations; classification was not qualified. Do not rerun T2. Preserve raw and first auditor result under [output/](output/) and see [STOP.md](STOP.md).
