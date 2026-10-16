# Bound authority issue API v1

Task: `O3-AUTHORITY-BOUND-ISSUE-API-20260916-006`  
Issue: #201  
Immutable base: `71ab480b5a9b74e54ebae06a70913bb94ea432ef`

## H

After #194 proved that identity binding must precede byte-bound durable issuance, test the minimum ordering mechanism: one project-facing wrapper owns `issue(receipt, terminal)`, first binds the runtime authority identity, and passes only the returned bound copy to the retained byte-bound ledger. No retained binder, validator, or durable-token implementation is changed.

## Frozen candidate

`bound_authority_issue_v1.py` SHA-256: `2f812a678b72f09985e24d003b2e7030508a49e4475e9d3aef5533b1a07f2ba2`  
Formal runner SHA-256: `eabc8e41e57f57dd61eb36f9cec9d786ab20ce721e39a234f27cd2b29627e66e`

Exact retained dependency hashes were checked before the formal run, including binder `a305c1f7...`, byte-bound ledger `a0744260...`, bridge-v2 snapshot `f16ba93...`, durable-token v2 `72a34816...`, and bridge-v1 dependency `2c9684d8...`.

## First outcome

Result ID: `authority-bound-issue-api-v1-20260916-01`  
Formal retries: **0**  
Hard gates: **9/9 PASS**  
Decision: **`RETAIN_BOUND_ISSUE_API_V1`**

- Valid no-caller-ID input bound `runtime-intent-token`, issued sequence 11, and left the caller receipt unmodified.
- A forged caller ID was rejected by the identity binder with zero durable-entry mutation.
- Release/interruption intent-token mismatch was rejected with zero durable-entry mutation.
- A bridge-v2-invalid receipt that passed identity binding was rejected by the byte-bound validator with zero durable-entry mutation.
- Restart recovered the same pending runtime ID and sequence.
- Duplicate issue rejected while preserving exactly one pending entry.
- Consume followed by restart remained consumed.
- `after_temp_fsync` delegated crash left no issued entry after restart.
- `after_replace_fsync` delegated crash raised but restart recovered the durably issued runtime ID, preserving the retained durability semantics.

Formal-result SHA-256: `8abdf538c762b6e31d858439202e729b23119ef58287f07fe5cfb008c7df99c3`. Independent audit: PASS with no errors.

## D

Retain the wrapper as the current minimum project-facing composition boundary for offline work:

`runtime terminal identity bind -> byte-bound receipt validation -> durable token issue`

This result narrows the caller surface and removes the ordering footgun demonstrated in #194. It does **not** make the underlying Python ledger inaccessible to arbitrary in-process code.

## C

The wrapper currently imports the retained identity binder normally. The durable ledger sidecar pins the receipt-validator bytes, but this wrapper does not durably pin the binder bytes. Therefore a restart under changed binder source could alter which top-level identity is accepted while the validator pin remains unchanged. That question was intentionally not changed in this experiment and is the highest-information successor.

## U

Offline composition semantics only. No live GUI/model/network/durable-submit claim. PR #168 executed-source provenance remains independently unresolved, so this result does not authorize a live crash-after-send allocation.
