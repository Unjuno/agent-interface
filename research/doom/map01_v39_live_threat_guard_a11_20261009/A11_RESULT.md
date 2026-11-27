# MAP01 V39 live threat-guard A11 result

Allocation `map01-v39-live-threat-guard-a11-20261009` ran once on exact current main `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36`. The source freeze selected seed 990622, fixture `map01-threat-contact-v2`, model `gpt-5.6-luna` low, and a 32-decision cap. The run lasted 189.111 seconds; guest and app-server exited 0 with no relay error. A11 was not retried.

The episode completed 32 model turns alive but unfinished: two kills, zero deaths, and no MAP01 exit. Health ranged 64–100 and ammo 32–52. The joint gate was not exposed: zero hard-health guard events, zero useful scorer events during pending inference, and no bounded recovery after a guard. One useful scorer event occurred outside pending inference. A11 is allocation-scoped **HOLD**; it does not establish survival benefit, causality, event rates, or MAP01 completion.

The frozen original audit remains **FAIL**. Provenance, image custody, terminal completeness, per-key accounting, and final empty-release checks pass; its cancellation check requires a separate release event for all 32 cancellations. The additive admission-aware reconciliation accounts for 32/32: six active-input cancellations have matching token-bound owner releases, and 26 cancellations with no admitted input/interruption lease have verified-empty terminal receipts. There are no unaccounted cancellations. The controller-failure receipt is absent because the controller completed normally. The original FAIL remains alongside supplemental HOLD.

The full raw allocation remains local under `results-local/doom/map01-v39-live-threat-guard-a11-20261009/`. Its retained manifest covers 6,369 files totaling 132,258,932 bytes, with manifest SHA-256 `c874389581f10ab1f7e237ce9e2787166cf743dbaad3b448e32e93320671102a`. The public audit files are aggregate projections; raw transient intent tokens and per-key identities are omitted.

## Publication copy

The public runner and auditor derive and validate the host mount root from the nested checkout instead of embedding a machine-specific absolute path. This publication-only sanitization was made after execution, so their hashes differ from the exact executed files recorded in the local freeze. The public freeze redacts the old experiment-commit reference and host details. The exact run source, raw audit, original freeze, and output remain preserved locally; no claim is made that the public runner is byte-identical to the executed runner. No game/model was rerun during publication.
