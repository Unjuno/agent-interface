# Receiver restart / commit-before-seal-ACK — #4332

Allocation: seal-restart-20260925-sr61-01. Base: 46e85863a9d0bfa9f5b7648fd81f3423907ca106.
Own only research/concurrency/seal_restart_sr61_v1/** on research/seal-restart-20260925-sr61.
Preserve #4328, rf55, closed #544/#680 and all parallel results. rf55 was re-audited without actors; its LOCAL status is unchanged. Its original full archive is not part of this new study.

## H
Persistent exclusion must precede an externally usable cancellation receipt. EARLY_ACK exposes a refund whose uncommitted closure disappears at SIGKILL; COMMIT_ACK should preserve it through opening the same SQLite store in a new process. This is a known transactional ordering principle applied to evidence-budget recovery, not a new DB algorithm.

## T
24 fresh cases = six conditions x two arms x two repetitions. matrix.json fixes order and identities. Four immutable six-case batches: python -S -B study.py launch formal INDEX (0,1,2,3 separately). Each child batch bound30s, tool envelope40s; source gate plus final ownership reread before first execution. Stop on incomplete batch; no same-batch retry/replacement/exclusion/tuning. The sender/fault supervisor is one process, but refund() receives only the delivered receipt and expected session, not fault labels/DB state. Two actual receiver processes per case. Private stdin/stdout pipes; no socket network or GUI. Generated payload4096 bytes is test data, not fresh observation.

SQLite DELETE journal/FULL synchronous/explicit transaction; same session and original DB path across restart. Do not delete recovery journals. Both arms use the same HEADER-before-BODY receiver and received-body persistence; no independent receiver quota. Only closure commit/receipt order differs.

NORMAL_RESTART: complete closure then graceful restart. CRASH_AT_RECEIPT: kill immediately after the usable receipt, before granting its next phase barrier. CRASH_PRECOMMIT: kill at precommit before either receipt. COMMITTED_REPLY_LOST: suppress delivered receipt, finish transaction, then kill. PRE_RECEIVED: C0 is received before sealing; only C1 may refund, then graceful restart. FOREIGN_SEAL: foreign logical session is refused, then graceful restart.

Start with C0/C1 reservations8192. Refund matching CLOSED IDs once; RECEIVED never refunds. Admit C2/C3 subject to remaining CUE capacity8192, preserve AUTO0/AUTO1 capacity8192, then release original delayed HEADERs C0/C1. Whole-session maximum16384. Pre-received C0's later HEADER is a duplicate probe, never a second BODY. Complete last-hop decoded bytes are the endpoint; metadata/Base64/log/storage bytes are excluded. A destroyed connection is restored by the harness; no transport reconnect reliability claim.

## D
PASS_COMMIT_BEFORE_SEAL_ACK_RESTART_SCOPED requires all24 complete cases/48 receiver exits/four observed batch exits and exact source/raw identities; EARLY_ACK exceeds16384 in exactly both CRASH_AT_RECEIPT cases, COMMIT_ACK has zero overages; AUTO0/AUTO1 exact everywhere; stable/foreign/pre-received controls match; no refund without a valid receipt; durable but unacknowledged closures retain underuse. Separate raw audit errors=[] and12/12 prospectively defined effective evidence controls rejected, zero no-ops/exceptions. Unexpected scientific contradiction is FAIL; provenance, missing row or audit/control failure is HOLD/STOP. All first records retained.

## C / U
Single trusted logical session, one live receiver, retained DB/tombstones, unchanged filesystem/path, successful commit and truthful receipt issuer. No restart of the sender, deletion/rollback of DB, GC, new-epoch installation, multiple writers, source authentication, partial BODY crash, power-loss durability, distributed exactly-once, model/human/task/latency/token benefit or runtime promotion. Process-kill exposure is not power failure. Same-author separate implementation is not independent human review; no calibrated combined uncertainty or coverage factor is fabricated. Phase barriers deliberately expose the boundary; no natural incidence estimate.

## Construction and roadmap
construction01 includes complete native rows but an auditor IndexError on absent COMMIT in a copied-evidence control. Preserve that auditor/partial controls. Before freeze, missing-COMMIT/receipt guards were corrected; process timestamp starts before Popen; construction02 completed24 rows,12 controls and10 unit methods. Construction is not held-out science. Next: public source readback -> four formal batches -> audit/controls -> full lossless evidence PR -> exact-head checks/scoped review -> qualified main readback. Global ROADMAP stays open.
