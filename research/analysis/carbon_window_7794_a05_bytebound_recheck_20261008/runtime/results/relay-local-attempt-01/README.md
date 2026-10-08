# Explicit host attempt identity

Primary use of main bd58ffb40 saved `http://n_p` correctly using summary replies and image review, but first failed to present a delivered observation because the caller used `reply.attempt`, which was absent. The original wrapper blocked further actions; its transport closed with exit 0. A new explicit connection to the same application observed again before input. The first connection made no input request. Both histories are retained, rather than counting only the successful connection.

Across both connections: five MCP calls (two observations, two dispatches, one close), two input programs, three rendered/reviewed images and no full retrieval. Independent file scoring ran after control ended and confirmed the saved value. All fixture children terminated; their individual exit codes remain recorded. The timing file covers only the second connection, not total task latency. No actual model token/cost measurement or speedup is claimed.

The instrumented host now returns an additional `attempt` alongside the unchanged relay response. `wait()` returns the same request promise/result. Callers use `present(reply.attempt)` and `review(reply.attempt, ...)`. The protocol ID may be reused after refusal, while this local attempt always selects the delivered retained file. Persisted reply bytes and MCP content remain unchanged. The base uninstrumented relay client is unchanged.

A regression that first refuses and then returns protocol id 1 failed before the fix because attempt was undefined. After the fix it verifies local attempts 1 and 2, correct presentation/review, same-promise waiting and unchanged raw reply. All 23 relay/timeline tests pass. These tests exercise transport semantics; the primary GUI run above predates the host fix and is motivation, not a claim of post-fix GUI validation.

`raw.tar.gz` contains the complete primary record including the first failure, portable artifact, fixture runner and before/after regression logs. `manifest.json` records hashes and byte counts for every archived file. No frozen allocation was rerun or modified.
