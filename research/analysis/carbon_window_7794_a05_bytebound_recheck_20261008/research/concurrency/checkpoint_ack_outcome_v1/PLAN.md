# Checkpoint commit-receipt boundary v1 — frozen plan

Issue: #4111. Allocation: `checkpoint-ack-outcome-20260922-01`.

## H/T/D/C/U

H: complete checkpoint bytes do not by themselves identify whether the worker's separately authoritative update commit occurred. A strict durable receipt bound to update id, base digest, target version and exact checkpoint digest can resolve commit-before-ACK loss and refuse published-but-uncommitted or mismatched states.

T: standard-library local process experiment. Three policies × ten fixed scenarios × three repetitions = 90 fresh cases. Each case has a private directory and SQLite DB. Atomic same-directory checkpoint publication is held fixed. Worker and recovery are separate subprocesses. SIGKILL is injected only at the two declared barriers. Formal runs once, no retries/replacements/tuning.

D: exact 90-case coverage; source/process/file/DB identities; candidate positives only NORMAL_COMMIT_ACK, COMMIT_KILL_BEFORE_ACK, DUPLICATE_IDENTICAL_RECEIPT (9/30); candidate unsafe advances 0; BYTES_ONLY unsafe advances 18/30; EXIT_OR_BYTES unsafe advances 15/30; duplicate receipt logical advance count exactly one; old checkpoint unchanged; neutral authority/task/replay flags; independent raw audit and >=10 corruption controls pass.

C: SQLite receipt is a deliberately stronger experimental contract, not a claim about historical #3911 or a required production implementation. Process kill is not power loss. No external effect or authentication.

U: trained state, power loss, multiwriter/distributed ACK, hostile records, external exactly-once effects, cross-platform, latency/tokens and production integration.

## Fixed order

For rep 0,1,2: scenarios in the order below; within each scenario policies are BYTES_ONLY, EXIT_OR_BYTES, COMMIT_RECEIPT_BOUND.

1. NORMAL_COMMIT_ACK
2. PUBLISH_KILL_BEFORE_COMMIT
3. COMMIT_KILL_BEFORE_ACK
4. PUBLISH_EXIT0_NO_COMMIT
5. STALE_OLD_RECEIPT
6. WRONG_DIGEST_RECEIPT
7. WRONG_UPDATE_ID_RECEIPT
8. BOOLEAN_VERSION_RECEIPT
9. VALID_RECEIPT_MISSING_CHECKPOINT
10. DUPLICATE_IDENTICAL_RECEIPT

Formal output directory must not exist. Any unexpected exception writes STOP.json and ends the allocation. Construction uses a separate directory and is excluded.
