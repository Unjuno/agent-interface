# Split binder/validator pin atomicity v1

Task: `O3-AUTHORITY-SPLIT-PIN-ATOMICITY-20260916-009`  
Issue: #211  
Immutable base: `71dea2279dd4b8fb5a1d6f64e7c773a756feeb5b`

## H

After #210, authority issuance has two independently durable policy identities: the identity-binder pin and the receipt-validator pin. The question was whether this alone requires an atomic composite manifest.

The narrower restart-state hypothesis was that separate pins are sufficient if no established token state can ever reopen under different binder or validator bytes. A partial initialization before token-state creation is classified separately from reinterpretation of durable authority state.

## T

A source-first, ten-case separate-process matrix used the exact retained #210 candidate and exact retained binder/validator/durable sources. A diagnostic validator source changed only byte identity by appending a trailing comment; executable policy was otherwise identical.

Frozen harness identities:

- diagnostic validator byte drift: `1f40ea48def2e99823c8e254dc1f95927d9c5600bfb3fc420185e76ca5f71a81`
- process worker: `1ad0ca3937e361f1e4e2fd98921649a50b03361157709228fd650f9faf81834b`
- formal runner: `d942dc75c19bb993b35ff919a944db84b3c0461ea53e96c970b64f218ff5defa`

## First outcome

Result ID: `authority-split-pin-atomicity-v1-20260916-01`  
Formal retries: **0**  
Hard gates: **10/10 PASS**  
Decision: **`HOLD_COMPOSITE_MANIFEST_NO_STATE_REINTERPRETATION`**

Observed sequence:

1. Exact binder + exact validator initialized and issued the runtime-owned token normally.
2. Crash immediately after binder-sidecar persistence left exactly one binder pin, no validator pin, and no token state.
3. At that pre-state point, retry with the exact binder plus the not-yet-pinned diagnostic validator was allowed to establish that validator as the first validator pin and then create token state. This is classified as initial configuration selection, not reinterpretation of prior authority state, because no token state existed before the choice.
4. Crash immediately after validator-sidecar persistence left both policy pins but no token state.
5. With both pins present, binder byte drift failed `binder pin mismatch` without changing either pin or creating state.
6. With both pins present, validator byte drift failed `validator pin mismatch` without changing either pin or creating state.
7. After complete token-state creation, binder drift failed closed without changing state or pins.
8. After complete token-state creation, validator drift failed closed without changing state or pins.
9. Existing token state with the binder pin deleted failed closed and left token state/validator pin unchanged.
10. Existing token state with the validator pin deleted failed closed and left token state/binder pin unchanged.

Formal-result SHA-256: `5597f0a61b70875313d9103e3a928d37318a5280b28a80546afea2d209eac23b`. Independent audit: PASS with zero errors.

## D

Do **not** add a composite manifest for restart-state continuity at this point. No tested crash/source-drift path can reinterpret an established token state under new binder or validator bytes.

The only mixed binder/validator pair appeared after a crash that had persisted only the binder pin and before any validator pin or token state existed. Under the current claim, that is a fresh completion of initialization. If the project later requires an externally authorized binder+validator bundle, the requirement should be stated directly as a trust/configuration property rather than inferred from crash durability.

## C

This result does not prove that every binder/validator pair is semantically acceptable. Separate pins preserve whichever pair becomes established; they do not provide a trust root or allowlist proving that the pair was approved.

It also does not cover malicious file replacement with filesystem-level capabilities, cryptographic authenticity, or multi-host distributed state. The evidence is local restart consistency under the retained fsync/replace persistence model.

## U

Offline separate-process evidence only. No live GUI/model/network/durable-submit claim. PR #168 executed-source provenance remains independently unresolved and continues to block the downstream live crash-after-send allocation.
