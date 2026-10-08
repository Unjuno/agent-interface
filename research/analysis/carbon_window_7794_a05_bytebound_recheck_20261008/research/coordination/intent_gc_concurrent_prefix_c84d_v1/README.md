# Issue #4037: concurrent intent compaction prefix

Retained decision: **PASS_CONCURRENT_COMPACTION_PREFIX_SCOPED**. Research evidence only; no production implementation or shared-runtime change.

The compactor captures frontier 3. When an actor accepts D4 before compaction, an atomic marker update followed by unrestricted history deletion can still erase D4. The exact archived #531 model then admits a rebound old identity and rejects genuine E5. Prefix-limited deletion preserves D4; transaction-local frontier revalidation instead safely defers changed-state maintenance.

Two fixed formal batches completed 18 cases / 54 independent database-copy probes / 90 worker processes, zero reruns. STALE_DELETE_ALL has 2 rebound admissions and 4 genuine-next admissions; BOUNDED_PREFIX and REVALIDATE_FRONTIER have 0 and 6 respectively. Exact unchanged old requests add no effect in every case. The revalidation method defers 2 maintenance operations; those are not successful compactions. Separate raw-only auditor: errors empty, 10 corruption controls rejected; 10 unit methods pass.

Read REPORT.md for full H/T/D/C/U, derivation, limitations and integration decision. PREREG.md includes the field/unit table. worker.py and the exact vendor531.py are directly readable. Complete remaining frozen source, all DB/raw/process evidence and both construction attempts are inside the lossless archive.

## Audit without rerunning the experiment

From this directory, with a fresh destination:

```sh
python -S -B unpack.py /tmp/issue4037-review
cd /tmp/issue4037-review
python -S -B audit.py .
python -S -B test_study.py
```

The extractor never runs study code. Do not execute the consumed formal batches or rewrite their freeze. PACKAGE.json binds eight binary fragments to the 44,792-byte archive SHA256 `4e8c5c66c0401eaaecdb6afb043fa7a6125de5e44e1f40a5dd8295634418ebdf`: 776 original files / 9,627,357 member bytes. Fresh extraction and read-only re-audit reproduced the original audit bytes. Hashes establish integrity, not authenticity.

## Chronology and limits

The preformal public hash commitment was commit `c896dd816006700f91618b39aa7b4d00b2600dbc` and Issue comment 5768288728. Full source bytes were local and hash-bound then; this publication delivers them afterward. Construction0 timeout (7 complete, 1 partial, 1 unstarted) and its original source remain unchanged; a prospective amendment enabled stdlib-only -S startup, then excluded construction1 passed. No construction rows are pooled with formal results.

The prior a61e crash-order study was re-audited read-only and summarized on #531. Its full prior archive remains conversation-hosted, NOT included here or claimed fully GitHub-published. This archive is complete for the new c84d study only.

Provided Linux x86_64 container, CPython3.13.5 / SQLite3.46.1, DELETE/FULL, same-epoch cooperative issuer. No Docker/OrbStack image-attested replication, model/provider, GUI/input, power-loss, natural race-rate or timing/token benefit claim. Same-author separate auditor implementation/process is not independent human review. All comparisons use atomic write transactions; deletion scope/precondition is the variable. Integration handoff: bound destructive retention to the validated prefix and test old-identity refusal and genuine-next-work liveness separately. Parent integration and the global ROADMAP remain uncompleted by this result.
