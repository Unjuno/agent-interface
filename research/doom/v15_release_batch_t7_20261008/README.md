# V15 release publication fault boundaries, T7

## H / T / D / C / U

**H.** The current-main backend's exact release publication path marks the full per-key batch before sending rows, but its delivery positions and failure ledger should make an actually missing row fail closed in the T5 adapter. If a sink accepts every row but raises after the final acceptance, all ordered rows remain available even though the producer records an unknown delivery acknowledgment; the adapter may produce only a row-evidence temporal association, never causal attribution.

**T.** Freeze current main `e627b8954ecfbdd90ccfe35a81441a00d88047c8` and backend blob `193c2bd231795e7ee57de64aedfd741c8b814013`. AST-execute the exact `_delivery_ledger`, `_set_delivery_state`, `_publish_release_batch`, `_publish_incomplete_release_batch`, `_finish_incomplete_release_batch`, and `_attach_delivery_ledger` methods. Inject failure on the second member of a two-key batch once before sink acceptance and once after the sink stores the row. Pass only actually stored rows to the frozen T5 adapter.

**D.** Before-accept failure must leave ledger states confirmed/unknown, one of two delivery rows present, and adapter output `HOLD_INCOMPLETE_RELEASE_BATCH / UNRESOLVED`. After-accept failure must leave the same producer ledger states but two ordered rows visible; any `TEMPORALLY_UNIQUE` result is scoped to those complete observed rows and must retain `causal_attribution=NOT_ESTABLISHED`. The audit records that the adapter does not consume the exception ledger.

**C.** Deterministic sink fault injection over exact backend methods and the frozen adapter; owner receipts and scorer event are synthetic.

**U.** No owner thread, physical key state, GUI, game, model, live threat, production sink, application consumption, or task effect was exercised. This does not establish that production telemetry has complete collection or causal correctness.

## Reproduction

From repository root run `python -B research/doom/v15_release_batch_t7_20261008/run_modes.py` and then `python -B research/doom/v15_release_batch_t7_20261008/verify.py`.
