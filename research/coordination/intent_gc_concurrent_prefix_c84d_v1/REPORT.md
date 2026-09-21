# #4037 — compaction must cover only its validated prefix

## Result

**PASS_CONCURRENT_COMPACTION_PREFIX_SCOPED** for `intent-gc-concurrent-prefix-c84d-20260922-01`.
Two prospectively fixed nine-case batches completed once,18 fresh databases,54 separately copied diagnostic probes,90 actual worker processes. Both supervisor receipts record exit0/timeout=false. No formal rerun, replacement, exclusion, pooling or postfreeze source/gate change. The independent raw/database audit returns errors[] and rejects10/10 corruption controls.

| Policy | Cases | Exact original D4 applied again | Rebound D4 applied | Genuine E5 applied | Maintenance deferred |
|---|---:|---:|---:|---:|---:|
| STALE_DELETE_ALL |6|0|2|4|0|
| BOUNDED_PREFIX |6|0|0|6|0|
| REVALIDATE_FRONTIER |6|0|0|6|2|

Both unsafe baseline rows are the declared ADMIT_BETWEEN_CAPTURE_AND_COMPACT cases. These counts are finite directed coverage, not a race-frequency estimate. All three policies use atomic marker+deletion transactions. Atomicity does not itself preserve a prefix captured in an earlier transaction.

## H / T / D / C / U

H: a new accepted receipt can be deleted beyond an earlier captured compaction frontier. Range-limited deletion preserves it; revalidation can instead defer stale maintenance.

T: exact archived #531 WatermarkLedger; local provided Linux x86_64 execution container, CPython3.13.5/SQLite3.46.1, stdlib-only -S -B. One actor and one compactor in separate processes, real pipe request/reply barriers and separate SQLite connections. Three policies, three schedules, two repetitions. State is reopened for every operation; three probe copies per final database prevent one diagnostic from influencing another. No GUI/OS input, model/provider, external-network experiment, installs or user files. Docker/image identity unavailable; no Docker/OrbStack replication claim.

D: full18/54 source/process/order/SQL/state/database gates passed. Exact D4 never adds an effect. Both candidates preserve E5; bounded-prefix always completes selected maintenance, while revalidation defers exactly2 changed-frontier cases without mutation. Comparator failure is not erased by hypothesis PASS. Timeout/missing evidence would remain STOP/HOLD; complete contrary behavior FAIL.

C: trusted monotonic issuer, one epoch, one compactor per case, private DELETE/FULL SQLite, read_uncommitted off. Compactor capture is a completed read transaction, not a lock spanning the later actor commit. No claim of an SQLite defect, general concurrency solution, or a deployed production defect. Full prefix deletion is a NEW adapter, not a previously promised #531 capability.

U: no concurrent compactors, issuer restart, version reuse/ABA, arbitrary receipt authenticity, power failure, kernel/storage failure, physical input, actual model decisions, natural workload or latency/token benefit. Same-author independent implementation/process is not independent human review. Field/unit table is in PREREG.md; all ordering/ordinal gates are exact. No calibrated combined uncertainty or coverage factor is manufactured.

## Source-bound explanation

1. A1/B2/C3 produce generation4, retainedB2/C3, retired-through1 under the unchanged capacity2 model. The compactor records frontier3 and ends its read transaction.
2. A separate actor accepts D4, committing generation5, retainedC3/D4, retired-through2. Its actual request/reply and committed state are retained before compaction begins.
3. STALE_DELETE_ALL atomically writes retired-through3 and removes ALL receipts. It leaves generation5 but no D4 receipt. The unchanged model now derives next sequence4 from watermark3. Consequently a new wire using old D4 identity but generation5->6 is admitted; genuine E5 is refused as SEQUENCE_GAP.
4. Exact unchanged D4 still declares generation4->5. That original wire is rejected by the generation check and never adds an effect. This is not evidence that byte-identical retries always duplicate.
5. BOUNDED_PREFIX saves watermark3 but deletes only sequences through3. D4 remains, so the next sequence is5. Exact D4 is recognized, altered D4 conflicts, and E5 is admitted.
6. REVALIDATE_FRONTIER compares current frontier4 with captured3 in the compaction write transaction and rolls back the maintenance request. It retains C3/D4 and allows E5. Safe deferral is not claimed as completed compaction.
7. In BEFORE, captured frontier4 covers the already admitted D4; in AFTER, D4 is admitted after compaction. Both controls preserve the next sequence under every method. They distinguish stale captured scope from deletion itself.

Conditional design argument: with monotonic non-reused sequences, monotonic MAX watermark updates and serialized deletion/admission, deleting only through an observed accepted prefix cannot remove a later accepted ordinal. The current frontier remains represented either by a surviving later receipt or by the stored marker. This argument does not establish authenticity, multi-epoch behavior or availability under arbitrary corruption. Ordinals compare to ordinals; generation is a separate dimensionless field and diagnostic nanosecond clocks never create authority.

## Verification and retained failure

Public preformal hash commitment: commit c896dd816006700f91618b39aa7b4d00b2600dbc, FREEZE blob23263acc1addc33da02dea469048ee27edbac5b7. #4037 comment5768288728 fixes commands, denominator and the RPC-versus-lifetime clarification before formal execution. Complete source bytes are published with this report, not retrospectively claimed to have been remote before measurement.

Construction0 stopped at25s with7 complete/1partial/1unstarted; actual runner exit-15, timeout=true. Its original source and all available outputs are unchanged in the bundle. The prospective construction amendment then disabled optional site startup for this stdlib-only code. Fresh construction1 completed9 cases/27 probes, exit0; its samples are excluded. No scientific gate was relaxed. See CONSTRUCTION.md and the same Issue's run log; no wrapper-only successor Issue was created.

Ten unit methods pass, including independent oracle versus exact archived model, unchanged old-wire refusal, candidate fresh-work liveness, deferred nonmutation and typed comparisons. Formal audit verifies all recorded SQLite snapshots read-only against independently reconstructed primitive states, command/response/SQL joins, process identities and clocks. Ten corruption controls reject missing/duplicate cases, Boolean repetition/exit, changed watermark/effects/status/captured scope/deletion SQL and authority. Finite controls are not a proof of arbitrary auditor soundness.

Separate postformal re-audit returns exact original AUDIT bytes;384 formal files unchanged. All9 frozen source/plan/environment hashes unchanged. Ninety worker PIDs are absent at a later /proc check; recorded actual waits, not that later observation, establish process completion. No other process or branch was killed/reset.

| Artifact | SHA256 |
|---|---|
| FREEZE.json |23b07d2dda74656c24215a392188a679867fd0d73a372bccbc85fbe4dac63cfc|
| Ordered concatenation of both original RAW.jsonl files,269136 bytes |06f151d4f81710adecd7dbafc63214eeefe6d78e4c48461943781f5499ec16a5|
| AUDIT.json |6d0686164a8a7fc59fc672af16746e63d40ed7dbb7414e16a6d649445025743c|

## Prior work and integration handoff

#531's original model.py remains byte-identical,3639 bytes, SHA25625b0f18cd9d5fcfd69608810f0ea8f4cde60b076baa637f5dad5d4f1143507a7. It does not promise persistent concurrent compaction.

The previous a61e crash-order experiment remains separate. Its104924-byte conversation archive SHA256fc406d0cbdf58fc46dc6fd0f7620bb3315c9d29ac0ec3fba0313745e4a7b6a65 was restored and read-only re-audited in this session; the original AUDIT bytes match exactly. A retrospective result note was posted to #531 (comment5768244721). The FULL prior1151-file archive is NOT part of this new GitHub evidence bundle; its publication remains partial, not claimed complete. No old experiment is rerun or pooled.

Concrete #24/#2084/#2789 recovery requirement: bind destructive retention maintenance to its validated prefix, or revalidate the maintenance precondition transactionally. Test old-ID/content conflicts and genuine-next-work liveness independently. Do not infer a production solution from an archived class plus a research adapter. This issue is distinct from #4026's event ACK frontier, #4027's retired outcome query and #3991's initial effect/receipt commit.

Bounded scientific roadmap complete; PR/main delivery is tracked separately in the Issue. Global ROADMAP remains incomplete. Retained passes elsewhere do not establish same-model task quality/cost, human tempo or supported-backend coverage.

## Cross-domain application proposals

Database maintenance: retain records admitted after a compaction snapshot. Distributed work ledgers: preserve acknowledgement/dedup progress independently of removable payload. Agent recovery: distinguish status retention from authority to submit the next operation. These are transfer proposals, not measured production adoptions.

## Re-audit only

After verified extraction to a fresh directory:
```
python -S -B audit.py .
python -S -B test_study.py
```
Never rerun consumed formal batches or rewrite FREEZE.json. The extractor executes no experiment. Source hashes and archive hashes establish integrity, not source authenticity.

Primary context: https://www.sqlite.org/isolation.html and https://www.sqlite.org/lang_transaction.html . SQLite's per-transaction isolation is the implementation premise; the later application's deletion scope is the tested design choice.
