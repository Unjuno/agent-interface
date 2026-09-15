# Authority-ended receipt restart journal v1

Status: **PASS_RESTART_SAFETY / HOLD_CRASH_LIVENESS**.

Base commit: `a1ea4cbfac735eafb1f8901dd6c32a890bed015c`.

This is an additive, model-free offline follow-up to the retained live duplicate-receipt evidence at current main. It changes no shared runtime and consumes no GUI, OS-input, model, Doom, or formal efficacy allocation.

## Question

Current `ReplanReceiptLedger` remembers issued runtime-owned `authority_end_id` values only in process memory. The preceding live result explicitly left restart durability unproved and proposed the smallest next experiment: replay the exact retained receipt after a fresh ledger/process, then test the smallest rehydratable issued-ID journal.

## Exact inherited sources

The experiment copied three current-main files byte-for-byte into `upstream/` so the disposable container did not need network access:

- `authority_ended_bridge_v1.py` — Git blob `9fcfdce5229cb58b3d1a17aacbcef0cb44bd10f1`, SHA-256 `2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e`;
- `replan_receipt_ledger_v1.py` — Git blob `85ce5fb14767a35b28c5b6123393041aa1ae747c`, SHA-256 `7a45327f419e9188fde3b506c5402fc8f454127336c60c90035a8baf0dca9382`;
- `receipt-fixture.json` — Git blob `4070fd206c859357125a2cb327affa5aec6de8b8`, SHA-256 `fb5031a9aeb6b5ecd17d3cd65c5d6fd82b032abd848fc8f2548f14caafffc283`.

The copied Git-blob SHA-1 values were recomputed locally before measurement and matched all three current-main blobs exactly.

## Stage A — restart counterexample

Frozen preregistration SHA-256: `fe3b0a4ac7fd7a22ba31134f87f59a16738651205c55dec845f4062679016650`.

Runner SHA-256: `7961c033454a488983b025d03ba963f3791bb64b655cd391ead999cd027c6430`.

One first-outcome two-process test:

1. process A issued and consumed the exact retained receipt with `authority_end_id=9d0d4d9bad194302866da5edbaabcf61`;
2. process B started a fresh empty `ReplanReceiptLedger` and replayed the byte-identical receipt.

Result: process B **MINTED** another token with the same authority-end identity.

Decision: **FAIL_CURRENT_CANDIDATE_RESTART_REPLAY**. The in-memory ledger closes duplicate delivery only while its process state survives.

## Stage B — fsync-backed restart journal candidate

Frozen preregistration SHA-256: `1ececede59276aafe3ce51d79a68454afcf49d7831402d20b7f31cc24cb8144a`.

Candidate SHA-256: `861760bd6b2a95a7f0868f590e703644f363468ea8a047c3aeddc616b185d857`.

Runner SHA-256: `474a58682a31d7a6e3af31c87f8e4cb97077411feb28b1744a8b0698fbcb4aac`.

The candidate changes one mechanism: append a strict JSONL record containing only `authority_end_id`, flush and `fsync` it **before** returning `ReplanToken`, then reconstruct `issued_ids` from that journal after process restart. Malformed, duplicate, or unterminated journal records fail closed. The experiment assumes one writer; concurrent-writer locking is not added here.

All nine frozen rows passed:

| Case | Result |
|---|---|
| first issue persists | PASS |
| clean restart replays same receipt | rejected as duplicate |
| distinct new identity after restart | issued once |
| second restart replays distinct identity | rejected as duplicate |
| injected failure before persistence | no journal mark |
| restart after pre-persist failure | original receipt can issue |
| forced process exit after durable append but before token return | crash window reproduced |
| restart after that crash | same receipt rejected |
| truncated journal | fail-closed corruption error |

The two-ID clean journal SHA-256 was `7f4ec3c3b5649f631cd4d29ed966bfa04af69d52468f209f4e67a6c4abb72218`.

Decision: **PASS_RESTART_SAFETY_HOLD_CRASH_LIVENESS**.

## Why this is not production promotion

The journal fixes the scoped safety counterexample for a clean single-writer process restart, but it exposes the expected at-most-once liveness boundary. A subclass forced the process to exit immediately after the real `_persist()` returned and before `issue()` could return a token. The durable mark survived; after restart the exact receipt was rejected even though the caller never observed a token return.

Therefore client-side persistence alone cannot be described as exactly-once progress. Moving persistence later would reopen duplicate-action risk; persisting earlier can strand an unobserved issuance. Closing both requires a stronger recovery protocol, action-owner idempotency/transaction boundary, or an explicit policy that accepts safe at-most-once loss and reacquires fresh authority/evidence.

No claim is made here about power-loss durability, machine reboot, concurrent writers, network retry stacks, live input effects, model behavior, useful gameplay, or general exactly-once execution.

## H / T / D / C / U

**H.** Strict issued-ID persistence before token return prevents exact receipt remint across a clean process restart.

**T.** Exact retained receipt, byte-identical inherited bridge/ledger sources, separate Python interpreters for restart boundaries, one fixed first-outcome baseline and one fixed candidate matrix. Zero model/GUI/input calls.

**D.** Restart safety passes because both known identities reject after restart, one distinct identity issues once, pre-persist failure leaves no mark, and corrupted storage fails closed. Promotion is held because crash-after-persist-before-return strands liveness.

**C.** The candidate may only transfer the failure from duplicate authority to lost progress. A client-only two-phase state machine also cannot prove whether an external physical effect happened across its own crash without an independently idempotent/effect-owned boundary.

**U.** CPython 3.13.5, Linux 6.18.44, 5 visible KVM vCPUs on Intel Xeon Platinum 8573C; one local filesystem; no concurrent writer or power-loss fault injection. `fsync` returned successfully, but hardware persistence was not independently verified.

## Next smallest discriminator

Do not add a model. Test the crash cut points of a minimal two-phase issuance/consume journal and an effect-owner idempotency key separately. The key question is whether the runtime/action owner can make a retried execute identity return the prior terminal outcome without a second physical admission. If no such owner-side boundary exists, retain the client journal as fail-closed at-most-once safety and require fresh reacquisition after uncertain restart rather than claiming exactly-once continuation.
