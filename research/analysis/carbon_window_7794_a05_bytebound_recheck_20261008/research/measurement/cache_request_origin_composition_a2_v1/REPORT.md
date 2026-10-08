# Request-origin-bound cache composition — A2 first formal outcome

Decision: **PASS_CACHE_REQUEST_ORIGIN_COMPOSITION_SCOPED**.

One source-first formal invocation for Issue #1360; reruns/replacements/tuning **0**. No #1355 construction row/source was pooled.

## Formal

- independent microtraces: **150,000**;
- transitions: **600,000**;
- candidate/oracle result+state mismatch: **0**;
- stale in-flight responses refused: **20,000/20,000**;
- stale-origin cache installs/effects: **0/0**;
- fresh-after-invalidation installs/effects: **20,000/20,000**;
- replay attempts/refused/rebinds: **20,000/20,000/0**;
- HARD/AMBIG effects: **0/0**;
- duplicate invalidation double-advance: **0**;
- cross-scope mutations: **0**;
- generation-specific failures: **0** across all six frozen magnitudes;
- accepted authority promotions: **0**;
- negative INSTALL_TIME_ONLY stale semantic effects: **20,000**.

Independent audit PASS/errors[]. Five copied-result corruption controls reject. Postformal source hashes match the frozen source set. Result SHA-256: `7dc4504c564808984c5d0aa9acd620d808fc7687b43a50edfb66cda2a895d5ec`.

## Scope

Synthetic cache/currentness composition only. This establishes that request-origin identity is required to prevent install-time semantic laundering in this state model; it does not establish model quality, latency/token benefit, live-app transfer, or runtime promotion.
