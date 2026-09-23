# Analytical necessity witness for #1645

Assume intent change may occur before the new relevance receipt is published.
Let old intent `I1` use relevant tile set `A`, let new intent `I2` require tile `x` with `x ∉ A`, and let the old relevance generation remain `g` during the publication gap.

A relevance-only suppression function receives only:

`(scope, relevance_generation=g, receipt_relevance=A, changed={x}, critical={})`.

Immediately before the intent switch (world `W0`) this tuple is valid for `I1`, and `x` is irrelevant, so useful O3 gating should permit `SUPPRESS`.
Immediately after the intent switch but before relevance publication (world `W1`), the tuple is byte/field-identical, while `x` is relevant to `I2`, so safety requires `FORWARD`.

A deterministic function of the relevance-only tuple must return the same output in `W0` and `W1`. Returning `SUPPRESS` violates `W1` safety; returning `FORWARD` gives up the nontrivial `W0` suppression. Therefore relevance-generation binding alone cannot provide both properties under asynchronous intent→relevance publication.

A sufficient repair is to add a runtime-owned intent/currentness discriminator that changes immediately on intent switch. #1645 tests `intent_epoch`; an atomically invalidated broader observation/currentness epoch would be equivalent for this necessity result.
