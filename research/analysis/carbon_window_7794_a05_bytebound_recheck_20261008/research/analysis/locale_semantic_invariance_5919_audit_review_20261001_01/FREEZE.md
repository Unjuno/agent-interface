# Freeze — post-merge raw-only audit review for Issue #5919

- Allocation: POSTMERGE-RAW-AUDIT-5919-20261001-01
- Scope: independently verify retained T0 raw outputs and test actual mutated-result copies; this is not a new candidate/scientific allocation.
- Review base main: ee0bf5670c4f9cec0c1de1a0e966eb3dd6566c15
- Original T0 report/merge: PR #5923, merge commit 15658ee8c942ec8a8af7613f8e3f6722a377da6d
- Input blob identities at review base:
  - fixture.json: 56c39911c04f18a8ad338406ab02f777dc84893b
  - candidate_result.json: 34217b9165953ad3c6a6b582f0f1a77d3047f229
  - audit_result.json: ad21792d27781c87e0d7253e32610b21ea61fa3c
  - candidate.mjs: ed1e43d1447f497294ecab70ab04c420c899debe
  - audit.mjs (original): e9db35cd1fe18c8a7d7d1050cd21e2d1a7a117f8
- New raw-only review source Git blob: 9a81e043b7df6fb3372b2283f5e3006cd81aef6d

## H / T / D / C / U

**H.** A separate validator consuming only the frozen fixture and retained candidate result will accept the unmodified result, reject the three actual corrupted candidate-result copies represented by the frozen controls, reject duplicate/missing/extra case rows, and independently reproduce every declared decision and aggregate.

**T.** Execute only `audit_review.mjs` once against the exact GitHub blob bytes above, in one fresh Codex V8 isolate. Do not invoke the original candidate, original auditor, model, provider, GUI, application, or container. Mutate in-memory copies only; preserve original blobs unchanged.

**D.** `PASS_RAW_REVIEW` iff the original raw candidate is accepted against literal fixture cases, all three actual altered copies and all three structural coverage corruptions are rejected, and aggregate decisions match recomputation. Otherwise retain the exact failure. This does not retroactively make the original audit execute those probes.

**C.** Synthetic eight-case fixture; visual similarity is stipulated boolean fixture metadata.

**U.** No independent translation adjudication, rendered-image evidence, live application, model behavior, performance, safety, or product claim. This is audit-strengthening only, not a rerun or new H result.