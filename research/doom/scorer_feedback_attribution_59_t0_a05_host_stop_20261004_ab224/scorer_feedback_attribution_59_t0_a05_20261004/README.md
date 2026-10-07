# A05 — reject unknown positive scorer event kinds

## H / T / D / C / U

**H:** For the fixed `independent-progress-event-v2` producer contract on main `af6d0f9842a2377fba736d2d65643b02690f99d9`, a positive/useful event with an unregistered `kind` must not be promoted to a possible-intent envelope. The source-defined positive/useful kinds are `KILL_COUNT_INCREASE` and `MAP_EXIT`.

**T:** Preserve A04 unchanged. First run an expected-red unknown-kind probe against its exact source. Then run A05's v4 candidate on the same 100/200 ns scorer bracket and one verified ATTACK interval [90,210], using `BANANA_UNREGISTERED`; also verify both source-defined positive kinds retain the possible-envelope-only result.

**D:** `PASS_HOST_CONSTRUCTION_STOP_CONTAINER` only if A04 fails the unknown-kind expectation by emitting an envelope, A05 rejects it, the two known kinds remain `SINGLE_POSSIBLE_INTENT_ENVELOPE` with null `intent_token`, A04's 15 tests and A05's 2 tests pass separately, and compilation succeeds. Container failure is retained separately and is not a test pass.

**C:** This is a synthetic dictionary-level schema/semantic boundary. The event source is code-defined; this does not prove authentic producer provenance, session binding, scorer correctness, input occupancy, causal attribution, task effect, useful-feedback latency, or recovery efficacy. A future event-kind extension requires a corresponding contract/version update.

**U:** Whether a downstream consumer treats `SINGLE_POSSIBLE_INTENT_ENVELOPE` as positive progress, and what authenticity boundary binds serialized events to the producer, remain open. The test only proves the helper's disposition for the supplied event dictionaries.

## Execution

Base: PR #7537 head `8ddf0925539d03733d803b469586fb74a5b444e0`; current main producer contract: `af6d0f9842a2377fba736d2d65643b02690f99d9`, source SHA-256 `3d906a7043f0d674bac3bd137952adeac11c77c9339bc38ef6ca37b05e0d1613`.

The initial A04 probe failed as expected: it emitted `SINGLE_POSSIBLE_INTENT_ENVELOPE` for `BANANA_UNREGISTERED`, with `intent_token: null` but `possible_intent_tokens: ["intent-a"]`. Its original probe source is preserved in `initial-red/` and hash-bound in `FREEZE.json`. The minimal v4 change rejects unregistered positive/useful kinds while leaving the two recognized positive kinds' scoped envelope semantics unchanged. Red/green stdout and stderr, exit codes, source hashes, and both suite results are embedded in `RESULT.json`; `audit.py` checks those records read-only.

OrbStack Docker could not provide an image: both image listing and pull failed with containerd blob-open `operation not supported`. The probe and 15+2 tests therefore ran on host Python 3.14.5, not in a container. No game, model, GUI, input, or live allocation ran. This is a scoped construction result and does not close #59.
