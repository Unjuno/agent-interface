# Runtime intent-token binding for cross-domain `authority_ended` receipts

Status: **RETAIN_INTENT_TOKEN_BINDING** in one frozen 13-case offline formal matrix. No live GUI/model/network/durable-submit execution and no production promotion.

## Trigger

Issue #171 isolated a cross-domain composition gap: the truthful Inkscape two-capture `authority_ended` evidence can satisfy a bridge-v2-shaped validator, but the retained durable token ledger still requires a top-level runtime-owned `authority_end_id`.

The repository already has an earlier rule from the receipt-replay work:

```text
authority_end_id = interruption.intent_token
```

`Lease` creates that intent token before the authority-ending event. The retained Inkscape terminal projection from PR #168 carries the same runtime token through input admission, the expiry interruption and the explicit release, but does not expose it as top-level `authority_end_id`.

## Question

Should the cross-domain path mint a new identifier at expiry, verified release or post-authority observation, or can it strictly bind the existing runtime authority-epoch identity only when constructing the caller receipt?

## Candidate

`bind_authority_end_identity(receipt, terminal)` performs no UUID generation. It accepts only:

- terminal `status=authority_ended`;
- nonempty `terminal.interruption.intent_token`;
- interruption record `reason=expired` with verified empty input state;
- verified empty explicit terminal release;
- explicit release `intent_token`, when present, equal to the interruption token;
- no conflicting caller-supplied `authority_end_id`.

It then copies that exact runtime token to `receipt.authority_end_id`.

The bridge-v2 semantic snapshot remains a separate receipt validator. The retained durable-token state machine is unchanged; only its statically imported validator is replaced in the test harness so identity binding is the isolated variable.

## Frozen formal allocation

Result ID: `authority-end-identity-binding-v1-20260916-01`.

The source and preregistration were committed before the formal run. Formal retries: **0**.

Source SHA-256:

```text
a305c1f70bc7bf849421ad41a7539966d539e1037f7db2fa5116b41af4f5f730  authority_end_identity_binding_v1.py
f16ba93fabef5c395b349d91e2ea9ec4139f6f993a763269879fc8ccd6ee35f9  bridge_v2_semantic_snapshot.py
2bff1613ebd5ac89894d081bfc813a3f4c608669e8ca7dd09ebd7cd27ba47a22  retained_terminal_fixture.json
6b36dd5f88a89a0c1c1c683b3d4cd54306d415c32ae9c84f6200d4cec550b87f  formal_runner.py
72a3481653cf9c41ec1a03f4c7a7bf1c482ff69468b5d92986bad8cf814950b4  retained durable_token_state_v2 dependency
```

## First formal outcome

**13/13 PASS. Decision: `RETAIN_INTENT_TOKEN_BINDING`.**

The exact retained runtime token is `c516e6cfcf8041e0b1f68cdadd1dc265`.

Hard outcomes:

- truthful two-capture authority-ended receipt binds exactly that existing token;
- the token is already present in `input_stopped` before the first post-authority capture;
- durable issue stores the exact ID with `post_sequence=11`, status `pending`;
- byte-equivalent duplicate receipt is rejected;
- the same ID with an altered but otherwise bridge-valid post sequence is still rejected;
- restart reconstructs the pending token with the same ID and sequence;
- a distinct runtime intent token with a later sequence can issue separately;
- missing token, forged caller ID, legacy `expired`, unverified interruption, non-expiry interruption and release/interruption token mismatch all fail closed.

The retained timing projection places `input_stopped.emit_ns=7,902,026,788,372` before the first post-authority capture at `7,902,115,266,398`: the authority-epoch identity therefore existed about **88.478 ms before** that capture. This is descriptive evidence from the retained projection, not a real-time guarantee.

## Interpretation

A new authority-end UUID generator is not justified by this evidence. The cleaner contract is:

1. runtime allocates one intent token for the authority epoch before input;
2. input/release/interruption records preserve that identity;
3. only after a verified scheduled authority end and valid post-authority evidence does the caller-facing receipt expose the same token as `authority_end_id`;
4. durable token issuance remains keyed by that runtime identity.

This avoids introducing a new crash window solely to mint an identifier after release or after observation. It also makes caller-forged identity substitution explicitly invalid.

## Remaining blockers

This result does **not** close the live Inkscape composition yet.

1. `durable_token_state_v2.py` statically imports the old one-capture bridge-v1. A versioned validator boundary is still needed before truthful two-capture receipts can enter the durable state machine without test-harness monkeypatching.
2. PR #168's retained formal result remains a data source only here. Its formal executed-source provenance is independently unresolved; this experiment does not certify it.
3. No durable-submit transport or crash-after-send path is exercised here.

## H / T / D / C / U

**H.** Existing runtime `interruption.intent_token` is a sufficient authority-end identity; no fresh ID must be generated at authority loss/release/post-observation.

**T.** Frozen 13-case offline matrix over the retained two-capture terminal projection plus the retained durable-token state machine. Zero formal retries, no live input.

**D.** **RETAIN_INTENT_TOKEN_BINDING** because valid cases preserve the exact runtime token through issue/duplicate/restart semantics and all forged/non-authority-ending cases reject before token issuance.

**C.** This would fail if one intent token could legitimately represent multiple independent authority-ending epochs. The same-ID altered-terminal control is deliberately rejected; a genuinely distinct epoch requires a distinct runtime intent token.

**U.** One retained Inkscape terminal projection and one durable state implementation; offline only. PR #168 source provenance and live cross-domain timing remain separate uncertainties.

## Next smallest experiment

Do not run a live crash test yet. Version the durable-token validator boundary without changing its persisted state schema: compare the current hard-import bridge-v1 ledger against a candidate that accepts an explicit validator callable/frozen validator version. Require legacy one-capture and truthful two-capture receipts to issue under their matching validators, while validator mismatch, downgrade, forged identity and restart all fail closed. Only after that and PR #168 provenance closure should live Inkscape durable-submit composition consume an allocation.
