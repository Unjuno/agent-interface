# Authority identity binder ordering v1

Task: `O3-AUTHORITY-ID-BINDER-ORDER-20260916-005`  
Issue: #194  
Branch base: PR #191 head `38048665ee020f6bd4e790807836a1a81649b0a7`

## Question

Does the byte-bound durable-token ledger itself establish that a top-level `authority_end_id` belongs to the runtime authority epoch, or must the retained identity binder run before durable issuance?

## H

Identity binding is a mandatory precondition to durable issuance. The byte-bound ledger correctly pins receipt-validator bytes, but its `issue()` method only requires a nonempty top-level `authority_end_id`; it does not prove equality with `terminal.interruption.intent_token`. Therefore a direct caller can persist a forged ID. Binding after that write is too late.

## T

A preregistered six-case offline/model-free matrix used byte-exact retained sources:

- identity binder SHA-256 `a305c1f70bc7bf849421ad41a7539966d539e1037f7db2fa5116b41af4f5f730`
- byte-bound ledger v3 `a0744260a48b3575a451c63139fdb2fde898e0493317d1edd1d731ce3d227be5`
- bridge-v2 semantic snapshot `f16ba93fabef5c395b349d91e2ea9ec4139f6f993a763269879fc8ccd6ee35f9`
- durable-token state v2 `72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4`
- bridge-v1 dependency `2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e`

The formal runner was committed before execution. Formal runner SHA-256: `01a8fedb397997646febc96f3fa5beeed977cff31df6bff4807c0fd3121041e0`.

## D / first outcome

Result ID: `authority-id-binder-order-v1-20260916-01`  
Formal retries: **0**  
Hard gates: **6/6 PASS**  
Decision: **`RETAIN_BINDER_BEFORE_LEDGER_ORDER`**

1. Direct byte-bound ledger issue accepted `caller-forged-id` and durably persisted it as pending at post sequence 11.
2. The exact identity binder rejected that same forged ID with `caller authority_end_id mismatch`.
3. With no caller ID, pre-binding copied `runtime-intent-token` from the verified expiry terminal and the ledger issued exactly that ID.
4. A fresh ledger process recovered the same runtime ID and post sequence 11.
5. Running the binder only after direct forged issuance rejected the receipt but did not remove the already durable forged pending entry.
6. A release/interruption intent-token mismatch was rejected before any token-state file existed.

Formal-result SHA-256: `084dddcb939d2254696db545f8ed738285a7f5cca8d923d6f167cd3823070d22`. Independent audit: PASS, no errors.

## Architecture consequence

Do not expose `BytePinnedValidatorLedger.issue(receipt)` as the cross-domain composition boundary when `receipt.authority_end_id` can be caller-provided. The minimum safe interface must take the terminal evidence and receipt together and enforce this order internally:

`bind runtime identity -> byte-bound receipt validation -> durable token issue`

This is an ordering/composition requirement, not evidence that PR #191's byte-binding mechanism is wrong. PR #191 remains useful behind the required identity-binding boundary.

## C

The result uses constructed offline terminal/receipt objects. It establishes the interface ordering property only. It does not prove live runtime wiring, GUI behavior, model behavior, durable-submit transport, or external exactly-once semantics.

## U

PR #168 remains independently blocked by unreconstructible formal executed-source provenance. No live crash-after-send allocation should be consumed until that source-first evidence closure is repaired and the identity/validator order is represented by the live receipt path without caller monkeypatching.
