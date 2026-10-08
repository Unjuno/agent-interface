# #1880 Local auto-recommit versus opaque semantic YIELD boundary

H: LOCAL_COMPLETE validators may be re-evaluated locally on current trusted inputs and can mint a fresh commit when TRUE. OPAQUE_SEMANTIC approval is bound to an exact semantic-input fingerprint; after fingerprint change, old approval alone is non-identifying and requires YIELD_FOR_APPROVAL. Exact unchanged fingerprint may reuse a still-valid approval receipt.
T: fingerprints {0,1,2,3}; all16 deterministic local predicates; all16 hidden semantic validators grouped only by observable old approval; projection p(x)=x mod2 comparator; ALWAYS_YIELD comparator; independent truth-table audit.
D: local/direct mismatch0; local safe auto cases>0; every changed opaque fingerprint class ambiguous; opaque changed auto0/yield>0; exact reuse>0; projected comparator unsafe>0; always-yield false yields>0; formal1/reruns0.
C: opaque semantics may later be compiled into a complete deterministic validator, changing type; receipt/model/rule expiry need explicit identity.
U: analytical recommit/YIELD boundary only; no model quality/token/latency/runtime/GUI/task/product claim.
