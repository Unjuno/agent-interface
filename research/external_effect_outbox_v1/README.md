# External-effect rollback boundary and crash recovery

**Retain outbox + receiver idempotency for this cooperative finite fixture; hold generic GUI/production promotion.**

Issue #228, successor to #197/#220 and geb-v3. Immutable experimental base `29a9c45c87cf59d6d9116b157eed6e737b1311f3`; source head `3773a1c76ece612a295a1a931c09aed68a09a71d`. The original source branch was merged by a parallel maintenance agent as PR #233 during results publication. Results branch descends from the same fixed source head, without rebasing or rerunning.

## Actual experiment

Run unchanged `compiled_gui_interface_v1.py` (original blob `0c02db714127c8e0f770f9d4ac03699749899d2b`, 17,726 bytes) with a new local adapter. A separate localhost HTTP receiver owns a second SQLite database. The receiver's committed effect row is external to the sender's rollback boundary. No real external service, GUI, model or user data is involved. Input release is a simulated adapter contract.

Primary completed allocation eeo-a2: two strategies, five scenarios, ten repetitions = 100 initial runtime calls and 100 predeclared recovery processes. Strategies: inline delivery before local commit; transactional outbox (command + pending delivery committed together before dispatch). Scenarios: stable; plan invalidated before final validation; abrupt process exit before local commit; exit after local commit; exit after receiver commit but before durable sender acknowledgement. Exits are actual child-process `os._exit(73)`, not modeled return values.

After the duplicate result, eeo-b1 changes only the receiver's existing deduplication switch: same code, five scenarios, ten repetitions, outbox only = 50 initial calls and 50 bounded recovery processes.

## Observed results

Each column has 50 completed cases. Counts are finite injected outcomes, not natural fault rates.

| Metric | Inline | Outbox | Outbox + receiver dedup |
|---|---:|---:|---:|
| Receiver effects without committed local commands | 20 | 0 | 0 |
| Additional duplicate effects after recovery | 0 | 10 | 0 |
| Committed commands undelivered before recovery | 0 | 10 | 10 |
| Committed commands undelivered after recovery | 0 | 0 | 0 |
| Invalid-plan effects | 0 | 0 | 0 |
| Initial runtime terminal receipt absent | 30 | 30 | 30 |

Inline's 20 orphan effects occur at two ten-case pre-local-commit crash boundaries. They are not called stale-plan effects: the violation is a remote effect with no durable local command. Outbox prevents this, and recovers all ten committed-but-unsent commands. But its ten post-receiver/pre-durable-ack crashes create twenty effects for ten commands after replay. Receiver deduplication preserves ten effects for those ten commands.

All 90 crashed initial runs lack a terminal receipt. Do not relabel them SAFE_YIELD. The 60 remaining receipts are 30 TASK_SUCCEEDED and 30 invalid-plan SAFE_YIELD; that distribution alone does not score external-effect consistency.

The HTTP acknowledgement is received before the injected post-receiver exit; the missing item is its durable sender-side recording. This is not a real lost-packet experiment.

## Key/payload binding control

Ten keys, each sent as original / identical replay / changed-payload replay: 30 HTTP requests, ten effects, ten duplicates suppressed, ten changed-payload requests rejected with HTTP 409. Same-key/different-action requests are not silently accepted.

## Audit and retention

Independent audit.py imports no controller. Both complete allocations pass event, snapshot, saved sender/receiver DB, payload, ID, ordering, source and receipt consistency checks. Five corruption classes are rejected in each completed allocation. `SUMMARY.json` retains the audit outputs. `OBSERVED_LEDGER.json.gz` losslessly contains the per-case measurements, including a separately marked 22-row incomplete prefix. The uploaded compressed blob was checked against its locally computed Git blob; an earlier mismatching transfer was not attached to any tree.

The full archive of 2,736 files (databases, logs, snapshots, sources, manifests and the first incomplete run) is a conversation attachment, not stored in this GitHub tree. `ARTIFACTS.json` fixes its SHA-256. Do not call the compact ledger byte-complete raw retention.

## First outcome and operational corrections

Initial eeo-a1 is INCOMPLETE: supervisor timeout after 22 complete cases; case 023 has initial/recovery receipts but lacks final snapshot/completed marker; 77 cases unstarted. The 22-case prefix audit passed. No pooling with eeo-a2/b1.

For eeo-a2 only supervision changed. An interactive-terminal attempt failed before any a2 trial. Actual supervision used bounded subprocess control (240 seconds) with active in-response polling. Experiment/audit/runtime hashes were unchanged. No experiment process remains running.

A failed ledger upload returned branch-not-found because another agent had merged/deleted the source branch via #233. Publication resumed from its retained exact head on a results-only branch. This was not a safety-check bypass, rebase or experimental retry.

## Environment / limits

AMD EPYC 9V74 reported by host, five visible logical CPUs, sampled 2596.132 MHz / unpinned; Linux 6.18.44; CPython 3.13.5; SQLite 3.46.1 WAL/FULL; HTTP/1.0 loopback; batch one. Timing endpoints use one host's monotonic nanoseconds for ordering only. No speed or token claim.

The outbox command is treated here as a durable decision at local commit. Receiver-side dedup is not semantic revalidation of a subsequently revoked plan. No receiver restart, power loss, partition, parallel dispatcher, arbitrary GUI or general exactly-once guarantee is established. The receiver is deliberately cooperative.

## H / T / D / C / U

H: local transaction validity is insufficient for independently committed remote effects; outbox addresses uncommitted-send/lost-send cases, while receiver idempotency addresses acknowledgement-gap duplicate application.
T: 100-case primary block; 50-case receiver-only successor; 30-request binding probe; fixed scenarios and ten repetitions; first unexpected harness failure stops the block.
D: retain these mechanisms at this finite boundary; reject outbox-alone as duplicate prevention; hold public ABI/GUI promotion.
C: dedup records lost or non-atomic with effect, IDs regenerated for retries, uncooperative receivers, or revocation after commit can break the conclusion.
U: controlled process exits, local SQLite and finite fault schedules; no natural probability estimate or calibrated timing uncertainty.

## Field definitions

All counts and IDs are dimensionless. `local_initial/final` count committed sender commands before/after recovery (integer 0 or 1). `receiver_initial/final` count receiver effect rows (nonnegative integer). `pending_outbox_initial` counts committed pending deliveries. `terminal` is the exact first runtime outcome or null if absent. Enum dictionaries are embedded in the ledger. Clock values in the complete archive are stored in ns (SI base unit seconds); comparisons use the same host clock.

## Reproduce

From this directory, inspect retained measurements without executing a new experiment:

```sh
python unpack_ledger.py
python audit_ledger.py
```

For new experiments, use fresh output names and an adequate outer execution limit:

```sh
python experiment.py run results/reproduce-a
python audit.py results/reproduce-a
python experiment.py run results/reproduce-b --dedup
python audit.py results/reproduce-b
python binding_probe.py results/reproduce-binding
```

Existing output directories are rejected. Runtime bytes are hash-checked on every worker import.

## Known mechanism references

SQLite transaction documentation: https://www.sqlite.org/lang_transaction.html
AWS transactional outbox pattern: https://docs.aws.amazon.com/en_en/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html
These explain known mechanisms; they are not sources for the project's local measurements or novelty claims.

Next question: when a GUI command cannot remain valid from commit until delayed delivery, what must the effect owner revalidate at delivery time?
