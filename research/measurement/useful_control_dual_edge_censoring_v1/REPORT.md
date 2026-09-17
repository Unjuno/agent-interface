# Dual-edge useful-control censoring — first formal outcome

Decision: **PASS_DUAL_EDGE_CENSORING_SCOPED**.

Exactly one frozen formal invocation was executed. Reruns, replacements and tuning: **0**.

## Result

- 30,000 fresh small-domain cases: candidate physical lower/upper bounds exactly equal the exhaustive minimum/maximum occupancy over every feasible exact down/release realization: **30,000/30,000**.
- 30,000/30,000 small-domain cases: candidate authority lower/upper bounds are conservative relative to exhaustive exact realizations.
- 50,000 fresh multi-actuation traces × 4 independently sampled exact realizations = **200,000** realization checks: containment failures **0**.
- Aggregate invariant failures: **0**.
- Frozen controls: projection discriminator, exact-edge reduction, overlap-zero-guaranteed, impossible-order rejection, nonblank ID rejection and duplicate-ID rejection all PASS.
- Independent audit regenerated both frozen corpora and reproduced digest `601136238be6c9c8240b8d8f9e1ae4dca505d95885972cabdfb38c5f7f7a83df`; audit errors `[]`.
- `FORMAL_RESULT.json` SHA-256: `16251d922225d3956f68425a9a6b05ea81306bbcc967f14d3e05874abf221f00`.
- `AUDIT.json` SHA-256: `1855a4ba728e0711f8756e3ba522e2abfeaa918c6cd763f889ee08700a179917`.

Diagnostic only: formal runner loop 5.354 s; outer wall 5.98 s; max RSS 93,100 KB in the execution container. No performance claim follows.

## Interpretation

The retained result establishes, for synthetic integer-time evidence, that a key actuation whose physical down and release transitions are both interval-censored can be represented without inventing an exact transition timestamp:

- guaranteed physical occupancy uses the latest possible down and earliest possible release;
- possible physical occupancy uses the earliest possible down and latest possible release;
- explicit authority intervals can be conservatively intersected with those envelopes.

This closes the representation gap exposed by current `input_owner_v10.py`/`input_owner_v11.py`, where `input_admission` brackets KeyPress with `admitted_ns`/`input_ack_ns` and `input_release_rpc` brackets KeyRelease+XSync with `call_started_ns`/`call_returned_ns`.

It does **not** establish that those runtime records are on an admissible shared clock, that record lineage is correctly paired across a real live session, that X11 physical transitions occur at a particular point inside the interval, or that any application effect is useful. #869 remains a separate live-X11 measurement lane and no #869 authority or case ID was consumed.

## Next discriminator

Before a live #869 formal allocation, test a read-only adapter from exact current typed `input_admission` + `input_release_rpc` record shapes into this dual-edge actuation contract. The adapter must fail closed on owner/intent/program/step/key/clock inconsistencies and must not synthesize missing down or release evidence.
