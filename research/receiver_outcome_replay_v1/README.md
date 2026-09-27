# Durable outcome replay after receiver restart

**RETAIN at this cooperative receiver-composition boundary; HOLD production/GUI promotion.**

Issue #331. Immutable experimental BASE: `c6d195473be0aa876cc991093262494209c7971f`.
Additive scope: `research/receiver_outcome_replay_v1/**`. No shared-runtime, GUI/model/formal allocation, workflow or historical result is changed.

## Question

PR #240 tested outbox crash recovery/idempotency; PR #251 separately tested first-delivery context-incarnation/predicate validation. What happens when a command commits, its response is lost, the context changes, and the identical command is replayed?

A replay asks what the earlier command did. A current refusal must not conceal a previously committed effect.

## One intervention

Both constructed policies use the same request fingerprint, private scope check, SQLite transaction, terminal-decision persistence, effect table and current-state diagnostic. Both compute current semantics. Only the **precedence of the returned verdict for an existing same-content command** changes:

- `validate_first`: current invalidity substitutes a refusal for the historical result.
- `outcome_first`: return the original durable result, report current validity separately, and emit no new effect.

This is a deliberate comparison fixture, not a claimed bug in a current project component or a third-party service. It is standalone receiver integration, **not execution of the unchanged compiled GUI runtime**. The private scope string is not a demonstrated authentication system. Real caller authorization must precede historical-result disclosure.

## Frozen final allocation

`outcome-replay-20260916-a3`: eight schedules x two policies x five repetitions = **80 cases**, three distinct receiver processes each = **240 invocations**. Fixed interleaved schedule, seed 34020260916, published before execution on #331.

The first process deliberately exits after commit-before-response in 70 cases, or before commit in ten controls. A subsequent mutation is followed by two fresh receiver processes reopening the same case-local DB. JSON stdin/stdout only; no network, real service, GUI, model or user-data operation.

Schedules: applied/stable; applied then predicate revoked; applied then generation replaced; applied then unrelated mutation; terminal rejection then predicate allowed; precommit crash then revocation; same ID/different payload; new ID after revocation. Rejection is terminal for its original ID in this fixture; reconsideration requires a new decision/ID.

## Measured result

| Metric | validate_first | outcome_first |
|---|---:|---:|
| Cases | 40 | 40 |
| Contradictions with original durable result | **10/25 historical replay cases** | **0/25** |
| Duplicate effects on recovery | 0 | 0 |
| New stale effects on recovery | 0 | 0 |
| Exact response-structure drift on next replay | **10** | **0** |
| Initial valid effects retained | 30 | 30 |

The ten contradictions are five applied-then-revoked and five applied-then-generation-replaced cases. The control returns REJECTED although the database retains an APPLIED decision and its effect. The candidate returns that original APPLIED receipt, separately reports current invalidity, and does not execute again.

The ten additional response-structure drifts concern new rejections after precommit rollback or under a new ID. Their later control responses omit saved fields but still say REJECTED: these are **not ten additional APPLIED/REJECTED contradictions**.

For the candidate, all five changed-payload cases return CONFLICT; all five new-ID-after-revocation cases reject; all five precommit cases have no old effect and reject under the new context; all five rejected-then-allowed cases retain the old terminal rejection. Stable and unrelated-change replay preserve the original result.

## Independent audit

The auditor imports neither receiver nor runner. All **80 cases**, retained SQLite databases, snapshots, process exit/stdout records and event ordering passed. **644 manifest files** verified; all five corruption classes rejected: fabricated acknowledgement, altered historical result, duplicate effect, authority flag and causal ordering.

Posthoc supplemental linkage checking verified 60 original effect contents and 90 final decision/request bindings. Published receiver/runner/auditor Git blobs were recomputed locally and match the executed source bytes. See SUMMARY.json and the full conversation archive.

## First outcomes retained

- a1: outer tool timeout, 11 complete rows, one incomplete case, 68 unstarted. Original auditor wrongly asserted repeat-response equality for the deficient control and failed two prefix rows.
- a2: receiver and runner unchanged; auditor v2 measures control response-structure drift instead of failing that assertion. Outer synchronous tool again interrupted: 14 complete rows, one incomplete, 65 unstarted. All 14 complete rows pass v2 row checks.
- a3: same receiver, runner, auditor v2 and schedule as a2; only execution supervision changes. All 80 cases complete. Runner exit 0; auditor exit 0. No experiment remains running.

No incomplete rows are pooled into the final result. Original sources, protocols and partial outputs remain in the full archive. Auditor v2 retains mandatory candidate/effect/source/order/content checks. Each successor was separately identified and frozen on #331.

## Environment and interpretation

Linux 6.18.44 x86_64 / glibc 2.41; CPython 3.13.5; SQLite 3.46.1 WAL/FULL; reported Intel Xeon Platinum 8573C, five visible CPUs, frequency unpinned. Timestamps support ordering, not speed claims.

Separate **historical command outcome**, **current semantic validity**, and **permission for a new effect**. Returning a past APPLIED result is not permission to run it again. New IDs and previously unseen commands still undergo current validation. Effect and decision must share a transaction.

Known idempotency mechanisms, not a novelty claim. Design context: [AWS Builders Library: Making retries safe](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) and [SQLite transaction control](https://www.sqlite.org/lang_transaction.html). The measured counts are local evidence, not results from those sources.

Limits: authored dependencies, cooperative local state, process crashes rather than power loss, no distributed transaction, no concurrent-client test, no record-retention expiry, no production authentication, no automatic dependency discovery, no GUI/model/token or natural-fault-rate claim.

## Reproduction and retention

Run `python verify_ledger.py` here to verify and decompress the lossless 80-row measurement ledger and recompute policy counts. This does not rerun any receiver and does not substitute for original-database validation.

`python prepare_protocol.py` reconstructs the byte-exact final protocol without executing trials. The published receiver/runner/auditor are directly readable. Full independent database/event/manifests audit requires the complete conversation ZIP listed in ARTIFACTS.json:

```sh
python receiver_outcome_replay_v1/a3/audit.py receiver_outcome_replay_v1/results/outcome-replay-20260916-a3
```

GitHub contains the complete a3 JSONL ledger but **not** the original SQLite files, individual event files or incomplete a1/a2 raw directories. Those are retained in the supplied 1,059-file archive. New execution needs a fresh protocol/allocation/output path; do not overwrite consumed IDs.

## Next single question

Two simultaneous identical deliveries against the same durable decision store. Sequential restart success does not establish concurrent admission behavior; keep the current semantics fixed.
