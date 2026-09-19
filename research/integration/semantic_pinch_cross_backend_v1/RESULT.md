# Semantic PINCH cross-backend lowering — retained result

Task `SEMANTIC-PINCH-CROSS-BACKEND-20260917-001`, Issue #681. Immutable publication BASE `387bf48955773f51c509d0a4b9eb3e39b593511c`.

## Decision

**`PASS_SEMANTIC_PINCH_CROSS_BACKEND_PROVENANCE_SCOPED`**.

One planner-facing intent was fixed with no backend/device fields: `PINCH(target=fixture-A, center_norm=[0.5,0.5], scale=0.5, contacts=2, authority_ms=1000)`, semantic digest `d5d8a164d189ef11dc54705866483240b260314590b01ac1b8b6f0042d9bb480`.

### Retained XI2 lowering (no live rerun)

The exact merged #655 witness Git blob `40b06a7447977d924cf0508d3035459cab9ef779` supplies four preregistered `pinch_complete` receipts. Each is normalized as two contacts, effect ratio 0.5, terminal neutral. No #655 measured ID was rerun.

### Fresh browser/CDP A2

A1 monolithic supervision is retained separately: 7 complete rows plus partial m08/no result, status `INCOMPLETE_SUPERVISION_TIMEOUT`, pooled rows 0. A2 changes supervision only and uses fresh n01..n08 IDs, one case per outer call.

- CDP touch: **4/4** observed simultaneous Touch IDs 11/22; independent PNG scorer measures red bar 200 -> 100 px (ratio 0.5); terminal touch/pointer sets empty; `SEMANTIC_EQUIVALENT`.
- Sequential mouse negative control: **4/4** touch events/IDs 0; independent PNG stays 200 -> 200 px; pointer neutral; `NOT_SEMANTICALLY_EQUIVALENT`.
- fresh A2 measured-ID reruns/replacements: **0**.

Frozen audit: errors `[]`. Supporting postformal verifier independently re-scores PNG bytes, touch logs, source hashes, A2 schedule and A1 non-pooling boundary: `PASS_POSTFORMAL_VERIFY`. Four copied-evidence corruptions reject 4/4.

## Retained postformal/setup incidents

- Construction transport: enterprise Chromium policy blocked `file://` and loopback HTTP; `about:blank` + `Page.setDocumentContent` isolated that setup issue before formal.
- Remote source freeze: one monolithic binary blob and one 3-part attempt had Git-object mismatches and remain unreferenced non-evidence. Canonical 10 small chunks were 10/10 exact.
- First postformal verifier added an incorrect newline to semantic digest canonicalization and failed 8/8 identities; formal evidence was unchanged, verifier was corrected to the already-frozen compiler definition and then passed.
- First corruption-control copy harness tried to copy Chromium `SingletonSocket` runtime nodes and failed before any mutation verdict; minimal evidence-only copy then rejected 4/4 controls.

## Interpretation

A single backend-independent semantic PINCH contract can be bound to two genuinely different touch lowerings at retained/fresh evidence boundaries while the mechanically plausible sequential-mouse route is not laundered into semantic equivalence. The planner-facing intent remains backend-neutral; route/provenance lives in lowering/receipt evidence.

## Limits

XI2 and CDP positives come from different controlled fixture implementations. This establishes a scoped semantic/effect/provenance contract, not arbitrary-application route interchangeability, model benefit, production ISA promotion, native hardware touch, Windows/macOS transfer, or performance. Browser neutral state is application-visible, not hardware-state proof.
