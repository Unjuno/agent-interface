# Exact live Inkscape receipt → durable authority composition v1

Task: `O3-INKSCAPE-LIVE-RECEIPT-DURABLE-COMPOSITION-20260916-012`  
Issue: #221  
Immutable base: `0792fe8bbacb53073b7f818244b0bf52f9c20fe6`

## H

#217 retained a fresh source-first real-Inkscape ABI-v2 terminal/receipt with runtime-owned identity. This experiment asks whether that exact retained live evidence, without synthetic identity or another GUI run, composes through the retained identity binder, binder-byte pin, current ABI-v2 validator-byte pin, and durable token state.

## Frozen input and policy identities

Input formal result: `inkscape-abi-v2-source-first-live-v1-20260916-994601`  
Input SHA-256: `402f6320f7a87acd0540b9aab1cd2eee610fab73c9937c72a682b77f11e0e9f3`  
Runtime authority ID: `901e6ed15b87454fdbef7909c1e0f026`  
Selected post-authority sequence: `3`

Retained policy/state identities checked by the formal runner:

- binder-byte-pinned wrapper: `c725ca222920acf7dde9e5e0950a7178da92dbac41b49f65452acd0939241060`
- runtime identity binder: `a305c1f70bc7bf849421ad41a7539966d539e1037f7db2fa5116b41af4f5f730`
- current live ABI-v2 bridge validator: `37e544086fe70087c0a2e6c03ce8c42c1c5dd71989f7fe541eb9055b3551eb52`
- byte-bound validator ledger v3: `a0744260a48b3575a451c63139fdb2fde898e0493317d1edd1d731ce3d227be5`
- durable token state v2: `72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4`
- bridge-v1 dependency: `2c9684d8f731b36469df06532fc2ce566716c0380002d18da1f317814f7acb1e`

Formal runner SHA-256: `6e6ae05eaacb8e39b1dacd072f33186d225255f0ac776988ac1ac7a0dc7f830d`; Git blob `3e03482e50448f6653fdd888b9a2ae07225b3610`. The runner was committed before the formal execution and the container reconstruction matched that Git blob.

## First outcome

Result ID: `inkscape-live-receipt-durable-composition-v1-20260916-01`  
Formal retries: **0**  
Hard gates: **7/7 PASS**  
Decision: **`RETAIN_LIVE_RECEIPT_DURABLE_IDENTITY_COMPOSITION`**

Observed facts:

1. The exact #217 live result and all retained dependency hashes matched preregistration.
2. Issuance used the exact runtime-owned `authority_end_id=901e6ed15b87454fdbef7909c1e0f026` and post sequence `3`; caller receipt and terminal objects were not mutated.
3. The binder sidecar pinned the exact retained binder SHA `a305c1f7...`; the validator sidecar pinned the exact current live ABI-v2 bridge SHA `37e54408...`.
4. A fresh ledger reopen recovered the same pending runtime identity at sequence 3.
5. Exact duplicate replay rejected with `DuplicateReceipt` and left the single pending entry unchanged.
6. A forged top-level caller ID rejected in the identity binder with `caller authority_end_id mismatch` and left durable state unchanged.
7. Consume followed by a fresh reopen retained status `consumed`; `recover_pending` rejected with `TokenConsumed`.

Formal-result SHA-256: `48f884b7dce2bca727706faeb5f69ced60eb208497de3ff5a7cde81f8ceb228c`. Independent audit: PASS with zero errors.

## D

Retain this composition result. The ABI-v2 → durable-token identity/compatibility gap is closed **as an interface/evidence composition property** for the exact retained live receipt: no synthetic ID is required, the runtime authority identity survives the binder/validator pins and restart, duplicate/forged identity are rejected, and consume is durable.

This result should supersede older compatibility probes that had to inject a diagnostic synthetic `authority_end_id` because the older live evidence did not carry a runtime-owned ID.

## C

The experiment replays exact retained live evidence offline. It does not prove that the full retained live servo/executor produces the terminal, binds identity, and persists the durable token in one continuous process execution. It also does not include durable-submit, network delivery, crash-after-send, or external exactly-once semantics.

Therefore this is not yet the authorization to run the downstream crash-after-send experiment. The remaining boundary is full-runtime integration, not ABI shape or durable-token compatibility.

## U

The next high-information experiment should isolate exactly one missing integration boundary: run the retained live runtime path through authority end and durable issuance in the same process, with no network send, then kill/restart around the durable issue boundary. If that succeeds source-first, only then compose with the already-retained durable-submit ordering for crash-after-send work.
