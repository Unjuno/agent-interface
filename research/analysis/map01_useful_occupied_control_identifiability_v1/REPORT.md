# #1838 Useful occupied-control identifiability

Decision: **PASS_USEFUL_OCCUPIED_CONTROL_NONIDENTIFIABLE_SCOPED**

The finite semantic model enumerated 8,100 latent worlds over physical occupancy interval, retained state-feedback time, latent causal source, and latent true useful-effect time.

Observed evidence models:
- BASE: 405/405 observation classes ambiguous;
- CAUSE_ONLY: 405/810 ambiguous;
- TIMESTAMP_ONLY: 1,485/4,050 ambiguous;
- BOTH causal action-effect binding + comparable effect timestamp: 0/8,100 ambiguous.

Thus interval-censored occupancy plus retained state-feedback cannot identify "useful occupied control". Causal binding alone is insufficient because useful-effect timing can fall before/during/after occupancy. Timestamp alone is insufficient because the observed change can be environmental/noncausal. Both are jointly sufficient for this scoped predicate.

Corruption controls reject laundering state feedback, viewport change, or terminal completion into a causal useful-effect receipt. Formal1/reruns0/replacements0/tuning0; independent audit errors0.

Implication: another posthoc intersection over current v38/v39 evidence cannot close the CURRENT_GOAL measurement gap. A later live instrument must record a causally bound first-useful-effect receipt on a clock lineage comparable to physical occupancy. This is an evidence-semantics result, not gameplay efficacy or human-tempo evidence.
