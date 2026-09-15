# Release-aware planner preparation v1

The client-wait v2 result exposes a bounded interval after physical input is
verified empty and before the prior program terminal arrives. This contract lets
a planner use that interval to prepare a candidate while preserving the later
terminal as a mandatory reconciliation boundary.

Preparation can begin only after the exact action-scoped, token-bound release has
been ingested. A prepared candidate is copied and deterministically fingerprinted.
It never grants input authority and cannot submit to Executor. After a matching
terminal arrives, the state becomes `PREPARED_REQUIRES_FRESH_ACTION_VALIDITY`;
the existing final-action-admission v2 boundary must still validate current
evidence and bind a fresh Executor acceptance.

Wrong-token or conflicting terminal evidence fails closed. The contract records
how much preparation overlapped the terminal wait without treating that duration
as useful work or a speedup. This is model-free construction. It has not yet run
an actual planner, reduced useful-action latency, or shown a token/task benefit.
