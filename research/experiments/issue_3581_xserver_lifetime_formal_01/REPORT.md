# Issue #3581 — scoped X-server lifetime matrix result

## Outcome

`PASS_XSERVER_LIFETIME_BINDING_REQUIRED_SCOPED` — one frozen `linux/arm64` container allocation, four paired Xvfb generations, 16/16 matrix rows, 28/28 negative controls, and a separate independent audit all passed. This supports a **typed recovery contract requirement** to bind a receipt to the lifetime of its X server in this deterministic fixture. It does not establish a production token implementation or product behavior.

## Reproduction and provenance

- Base commit: `61311817969251b814cb00b568a75c91a3591d3e`
- Image: `sha256:fa36aca92a682831d72b7e49bf05a9c6e31e68eadb06f3d2728360ceb1e9f6cb` (`linux/arm64`)
- Freeze SHA-256: `f2ddfb7587661e65cc7848de00546d803df1ffa30186db58475572f4afebe6ad`
- Source-manifest SHA-256: `bf2c917fa6cadd42aac285ab8c786442bb537d1b27867556b0222f1a52b4e3f0`
- Raw SHA-256: `371dc836a911537fadb417cbee0f2631ca13f53a07f885b451f559046172bbb6`
- Independent audit SHA-256: `6c6e3372f0d5b63b4e9966505db04df198716bdc3eab318e7201d4e8d4ce4a76`
- Formal invocation: exactly 1; reruns: 0; network: none; task input/action authority: 0.

The frozen merged #881 validator was copied byte-for-byte (`91983ab78a06b93cc7fdd829b6094fd255f18210`). Freeze↔manifest linkage, seven manifest-listed file hashes, and GitHub readback of all preregistration files were checked before the formal invocation. The raw's result self-hash and all frozen source hashes were checked independently afterward.

## Matrix

| Case | Policy | Rows | Typed classification | Admission |
|---|---|---:|---|---|
| Same generation | CURRENT_TYPED | 4 | EXACT_MATCH | ACCEPT 4/4 |
| Same generation | LIFETIME_BOUND | 4 | EXACT_MATCH | ACCEPT 4/4 |
| Stale G1 receipt against G2 | CURRENT_TYPED | 4 | EXACT_MATCH | ACCEPT 4/4 |
| Stale G1 receipt against G2 | LIFETIME_BOUND | 4 | EXACT_MATCH | REJECT 4/4 |

All four pairs independently recorded clean Xvfb exit and Unix socket disappearance before the next generation. Each pair reused root XID `543` and top-level XID `2097152`; backend, typed client ID and `KNOWN_NULL` transient evidence were equal, while process incarnation and random server token differed. Negative controls covered forged/missing tokens, unknown receipt, authority escalation, changed backend/client ID, and known transient mismatch (7 types × 4 repetitions); every control failed closed.

The corrected independent auditor did not import the runner or copied validator. It independently reconstructed the 16-row matrix, verified source/freeze/result hashes, and rejected all nine corruption challenges, including a forged PASS over a mutated cross-generation lifetime escape.

## Scope and next work

This experiment demonstrates a deterministic Xvfb counterexample to relying on the current typed identity fields alone after X-server restart, and a scoped discriminator that preserves same-generation acceptance while refusing stale cross-generation receipts. It does not implement production server-lifetime identity, prove secure token issuance/storage, test crash persistence, remote X11/compositors, native input admission, GUI effects, broad reliability, or efficiency.

The next research unit should implement or evaluate an actual non-receipt-mintable server-lifetime identity at the relevant recovery boundary, with negative tests for token substitution/forgery and lifecycle races. No production promotion is implied by this fixture result.
