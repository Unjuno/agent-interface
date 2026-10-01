# Membership validation → generation commit cross-file TOCTOU

Task `COORD-MEMBERSHIP-GENERATION-TOCTOU-20260916-015`, Issue #472.

Decision: **PASS_CROSS_FILE_TOCTOU_BOUNDARY_SCOPED**.

The experiment compares the already-retained membership-bound ALL-confirmed rule under two state layouts while preserving the same precomputed generation transition.

## First outcomes

| Case | Intervening membership change | Generation write | Final state |
|---|---|---|---|
| split stable | none | succeeds | epoch1 `{A,B}`, g2 |
| split race | epoch1 `{A,B}` → epoch2 `{A,B,C}` | **still succeeds** on separate coordination file | epoch2 `{A,B,C}`, g2 |
| unified race | epoch1 `{A,B}`,g1 → epoch2 `{A,B,C}`,g1 | **HTTP 409 stale-SHA reject** | epoch2 `{A,B,C}`, g1 |

The split-race outcome is the negative boundary: exact membership validation happened before the prescribed membership change, but the generation write used a different file whose SHA remained current. Therefore the membership change did not invalidate the stale authorization.

The unified record binds membership and generation to the same Git object identity. The prescribed membership update changed that identity; the pre-change generation write using the frozen old SHA was rejected by GitHub's contents CAS.

Measured commits:
- stable split generation advance: `510e4f7ce43f9522c34ca718512d2d59a293e4f4`
- split race membership change: `c7010b041413620e9d778f80dc0124adf06c1ace`
- split race stale-membership generation advance: `30f2bc4a959bf0c68182d60c00938e9514b0547c`
- unified membership change: `8e308e74d2a0a1e4b0327ae39e3e00f4b58cb19d`
- unified stale generation attempt: GitHub HTTP `409`, exact stale file SHA mismatch

Final Git blobs from branch readback:
- split race membership: `cbb981f90917535ba8fb8d7ebf6711c25598c72f`
- split race coordination: `cfaaa4fc010cb6c9b7d5dca119a058de99f0fad6`
- unified state: `22f610e978e6abd9f612656ac2d3f3e61a11b5ed`

## Interpretation

Membership validation and generation commit form one semantic transition. If they live in separately versioned records, a membership mutation can occur after validation without invalidating the coordination-file CAS. A single-record CAS closes this specific window because the membership mutation and generation transition contend on one identity.

This does not require the production representation to literally be one JSON file. An equivalent transaction token/compare-and-mutate owner could provide the same coupling.

## Limits

Sequential prescribed interleaving only. No simultaneous HTTP requests, distributed consensus, quorum availability, membership-change authorization, crash/power loss, multi-repository transaction, or production protocol claim. A separate external lock could also serialize split records; it was intentionally not tested.

`verify.py result.json` is a deterministic local consistency check. GitHub branch readback is the authoritative state evidence.
