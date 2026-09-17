# Epoch checkpoint restart durability — first outcome

Decision: `PASS_EPOCH_CHECKPOINT_RESTART_SCOPED`.

This experiment keeps the merged #1040 state semantics byte-exact and changes only persistence/restart. The candidate writes a canonical full semantic checkpoint to SQLite with rollback journal, `synchronous=FULL` and an explicit transaction. The writer subprocess exits completely before a fresh reader subprocess opens the committed database.

## First primary outcome

One frozen allocation used seed `104920260918001` for 20,000 cases. Fresh-process restore reproduced the exact pre-exit semantic view in **20,000/20,000** rows; restore mismatches0. `CURRENT_ONLY` checkpoints, which intentionally store only `latest_seq` and `latest_state_ids`, were insufficient in **20,000/20,000** cases because epoch2/historical-gap semantics were absent. Accepted-resync replay remained idempotent in256/256 held-out restored cases, and monotonic future append plus stale/nonmonotonic rejection passed256/256. Authority errors0. Writer reported7,547 cases with an epoch2 active overflow, so exact restore covers simultaneous epoch1 historical gaps and new active epoch2 incompleteness.

The fresh-process block completed in4.638s outer wall; `/usr/bin/time` observed5.23s and max RSS157,996KB. The committed SQLite database was79MB, SHA-256 `b9b81cf9a87f42e8df18578197e9662ff6983f891820601aa7934b99ca918bfb`; it is not Git-retained because the scientific result is represented by deterministic source/result/audit and the database size is disproportionate. RESULT SHA-256 `cbddaffd361d3f27d20ba71c76144bf4184ac81237e24c2c9a099c968b673553`.

Frozen audit over RESULT+database returned `PASS/errors=[]`. Construction controls6/6 covered exact restore, digest mismatch, schema mismatch, truncated payload, uncommitted transaction rollback and a true current-only negative representation.

## Audit limitation retained

Post-result corruption checks showed the frozen auditor rejects digest, exact-restore count, current-only discriminator count, decision and formal-invocation mutations (5/6) but does **not** compare RESULT seed to the frozen schedule. The primary was not rerun and the frozen auditor was not rewritten. A separately labelled posthoc integrity verifier was added to check `{seed,cases,formal_invocations,reruns,decision}` against `schedule.json`; it passes the untouched result and rejects the seed-mutated copy. This posthoc check is integrity evidence only, not part of the source-first scientific decision rule.

## Scope

This is committed SQLite process-restart evidence on one container host. It is not a power-loss, fsync/controller, distributed replication, live watcher recovery, planner-comprehension, task-correctness or production-ABI claim.
