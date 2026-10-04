# Session-bound A03 envelope guard — H/T/D/C/U

**H.** The latest scorer-attribution parent A03 correctly refuses a unique intent and causation claim, but its `possible_intent_tokens` can still name an interval from a different session if numeric clocks overlap. A session guard should reject that join while preserving A03's weaker envelope and endpoint-tie semantics.

**T.** At frozen parent `58102e6c12719ed5f4c4bb9616331d86b39ffa90`, compare the unguarded A03 function with an additive session-bound wrapper using fixed samples `[100, 200]`/event at `200` from `run-b`, plus interval `[90, 210]` from `run-a`. Also run same-session strict-envelope, same-session release-tie, and missing-ID controls.

**D.** `PASS_SESSION_BOUND_A03` iff unguarded A03 reports only a possible envelope (never a unique intent) for the cross-session fixture, the wrapper rejects the cross-session and missing-ID fixtures, the same-session result remains `SINGLE_POSSIBLE_INTENT_ENVELOPE` with no `intent_token`, and the endpoint-tie case remains `UNRESOLVED`. All outputs retain `causal_attribution: NOT_ESTABLISHED`.

**C.** `session_id` here is supplied by the caller; this test does not authenticate it or establish one common clock. A future live collector must bind run/source identity to scorer updates, events and input occurrences. Temporal envelope is not proof of held-key coverage, useful effect, or causation.

**U / STOP.** Synthetic local CPU construction only. No live session, game, model, GUI, physical input, recovery, survival or allocation was used. Docker image-store access is unavailable (`operation not supported`); #59's live lane is unassigned.

The prior `session_bound_v2/` experiment remains unchanged as its historical v1-API result. This A03-compatible successor supersedes that wrapper for the current attribution lineage.
