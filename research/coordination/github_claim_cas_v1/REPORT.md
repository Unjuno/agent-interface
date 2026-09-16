# GitHub stale-SHA CAS for one canonical claim record

Task `COORD-GITHUB-CONTENT-CAS-20260916-002`, Issue #349.

Publication BASE: `4e802fa2ec3c0c97545a38520bb18b3b126d8e4e`.
Pre-measurement freeze: `61e24d21e8a68e96250d2fdf36edc9549ce92a0f`.

**Decision: `PASS_SINGLE_PATH_GITHUB_CAS_SCOPED`.**

## Question

Issue #346 / PR #348 retained a deterministic pre-freeze duplicate-claim gate but left a check-to-claim race: two sessions can both read an apparently free state before either publishes. This experiment tests one smaller building block only: whether GitHub's file-content SHA precondition excludes a second sequential writer that still holds the old file SHA.

It does not test simultaneous requests or a complete lease protocol.

## Frozen setup

One dedicated branch and one canonical file:

`research/coordination/github_claim_cas_v1/claim_register.json`

Before measured updates:

- initial register blob `S`: `1cbfdaff3107aa947c9b24290d00c7bad68ce19e`;
- exact writer-A candidate: `aa2f3175865b6a996cfd28c886f083ac4a5a72c7`;
- exact writer-B candidate: `d44051d32719091d62032a86ea460cc1ac5b9ca2`;
- fixed order: A then B;
- both update calls required to present the same initial SHA `S`;
- no retry of B with a fresh SHA.

These identities and the gates were posted to Issue #349 before either measured update.

## First outcome

### Writer A

A presented the frozen initial SHA `1cbf...`.

GitHub accepted the update:

- commit: `ad61cb419276ec6507d06b3d0d7e904c8c34525e`;
- new content SHA: `aa2f3175865b6a996cfd28c886f083ac4a5a72c7`;
- new content SHA exactly equals the frozen writer-A blob.

### Writer B

B then presented the **same old** SHA `1cbf...`.

GitHub rejected the write with HTTP **409** and the returned message:

`research/coordination/github_claim_cas_v1/claim_register.json does not match 1cbfdaff3107aa947c9b24290d00c7bad68ce19e`

B was not retried with the fresh SHA.

### Final read

The final register blob is `aa2f3175865b6a996cfd28c886f083ac4a5a72c7`, byte-identical to writer A and not writer B. The recorded owner is `writer_a`.

Therefore the frozen stale-writer gate passes.

## Interpretation

The GitHub contents API supplies a useful **single-path compare-and-swap primitive** at this scope: a writer can condition its update on the exact file content it read, and a later writer carrying that stale file identity cannot silently overwrite the first writer.

This directly addresses one mechanical part of #346's TOCTOU problem, but not the whole coordination protocol. To benefit from it, all contenders must converge on the same canonical path (or another serialized resource) and must treat a stale-SHA rejection as a need to re-read/re-evaluate rather than as permission to force an update.

A whole-file register also introduces a new cost: two semantically unrelated claims can contend on the same blob even though #346's conflict rules would allow both. That is now the next discriminating question.

## H / T / D / C / U

**H — supported at single-path scope.** A succeeded from SHA `S`; B using the same stale `S` received GitHub HTTP 409; final bytes remained A.

**T — completed once.** One branch/path, fixed A->B order, exact frozen candidate bytes, two measured updates, one final read, no B retry.

**D — PASS.** All three gates pass: A success, B stale-SHA rejection from GitHub Contents API, final register byte-equal to A.

**C.** This is sequential stale-writer exclusion. The second request necessarily happened after A's commit. It does not prove how two truly simultaneous HTTP requests are scheduled.

**U.** One repository/branch/path/credential and one API implementation. GitHub availability, rate limits, permission changes, force-ref updates, multi-file semantics, semantic duplicate detection and conflict-resolution retries remain outside scope.

## ERROR CHECK

- Writer B was invoked exactly once with the frozen stale SHA and was not rescued with a new SHA.
- The HTTP 409 is distinguishable from a local connector safety refusal: the response cites the GitHub Contents API documentation family and the exact stale file SHA mismatch.
- Final file SHA was read after both outcomes and equals the pre-frozen writer-A blob.
- No main/shared-runtime/workflow file was changed; all writes are on the dedicated research branch.
- This does not claim simultaneous concurrency, distributed consensus, exactly-once allocation, or a deployable lease service.

## Next single question

When two **unrelated** claims race on one whole-file register, can a bounded stale-reject -> re-read -> semantic recheck -> merge protocol retain both safely, or does the coordination state need sharding to avoid unnecessary serialization?
