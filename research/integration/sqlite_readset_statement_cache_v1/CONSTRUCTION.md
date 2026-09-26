# Excluded construction log

Construction v0 (15 cases batched together) hit the external 40-second tool
limit after six completed RAW.json files and one started next case. There is
no EXECUTION.json or observed outer exit. A subsequent exact-path process scan
found no remaining worker, peer or runner. The six raw rows are cold controls,
not formal data. Preserve the partial path and four v0 sources.

Before any formal freeze, resident bounded peer IPC replaces six subprocess
launches per case; peer still opens a fresh SQLite connection for each operation.
The reader runs in a separate worker process. Fixed batches are reduced to six
cases and timed-out worker process groups are explicitly killed/reaped.
This engineering change is not a new scientific question or a successor Issue.

The first eight-method construction test suite had one FAIL: set_trace_callback
was bound to the original list.append, while prepare replaced that list. This
lost our SQL execution diagnostic, not SQLite's execution. Before freeze the
collector now clears the same list in place. Original policy/test/logs are
retained in construction-source-v1; no formal row existed.

The complete30-case construction has evidence errors0, but its initial proposed
scientific gate (both alternatives have zero false refusals) FAILS: NO_STATEMENT_CACHE
has one false refusal on view_retarget_old_resource. Its callback trace contains
both a.value and b.value, while the actual view result is b. The likely cause is
initial preparation followed by schema-triggered repreparation (consistent with
SQLite documentation); internal VM preparation was not directly instrumented.
The original CONSTRUCTION_AUDIT.json and v0 auditor are unchanged.
Before formal freeze, the scientific hypothesis is narrowed: uncached callbacks
must prevent missing dependencies/stale commits, with over-refusal measured and
reported separately, not required to be zero. METADATA_REUSE must preserve both
freshness and precision over this declared corpus. No policy implementation,
scenario, data or threshold was tuned to remove the uncached false refusal.
This is construction-informed preregistration, not a blinded replication.
