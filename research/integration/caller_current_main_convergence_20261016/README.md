# Current-main caller convergence and remaining integration gates

2026-10-16 JST, tested main `de7bcbf86316b312e3a34c9b15b07336caaa14ff`.
Ordinary local contract checks and saved-result review. No GUI, input, provider,
model, WSL/container or formal allocation was run. This does not replace the
historical Chromium comparison or qualify a new live comparison.

## Disposition of the old caller PRs

The current GitHub states of #7289 and #7310 are **closed, not merged PRs**.
Their heads are ancestors of the tested main, but ancestry alone does not prove
that their behavior survived later changes. The actual current caller and tests
were therefore checked below. Do not resume either old PR's reviewer-vote or
application-sender wait as a present requirement.

- Composition `df8e5fa1e1d5426d377c21fb1e23dd5c36ace14e` combines the caller
  repair family, including #7310 as its second parent, with deduplicated tests.
- `8e6673432e13e27c6fea5c3c8df9ee59b13ee9ad` rejects Boolean callback costs;
  #7632 subsequently merged the rescue/evidence branch into main.
- `ed326ccfeae1c66fde4ec38d0d3dcd9b54ca53d0` adds bounded effect evidence
  references. Current caller blob is `c903e7d1505a2ba98bdb21802302ab3b388fc4cb`.
  It is not byte-identical to either old PR's caller, and neither old test total
  is presented as current qualification.

[LINEAGE.json](LINEAGE.json) records live PR states, exact heads, main ancestry
and selected catalogue counts. No Issue/PR was closed by this batch. #57 remains
open; completed caller mechanics do not complete its live economic milestone.

## Executed checks and evidence

Nineteen selected modules, **76 methods, zero failures/errors/skips**, passed in
both ordinary and actual optimized Python. Eighteen selected modules are each
registered exactly once in the current integration catalogue; the supplemental
v2 yield-vocabulary check is selected here but is not in that catalogue. This is
not a run of the entire native/protocol catalogue or all platform tests.

[CONDITIONS.json](CONDITIONS.json), [SOURCE_PINS.json](SOURCE_PINS.json),
[PROCESS_RECEIPTS.json](PROCESS_RECEIPTS.json) and the complete stdout/stderr
retain commands, source identities and actual process/optimization results.
All 25 selected source/data files join the tested Git blobs to worktree contents
by AST or JSON semantics; Git-byte and worktree-byte hashes remain distinct.
The runner uses existing tests and synthetic adapter fixtures. It materializes
two committed retained JSON fixtures; it does not rerun their browser producer.

The 12 module ROWS/RECORDS groups retain **221 rows per mode**. Deterministic gzip
archives preserve the full JSON bytes, with uncompressed digests and sizes in
[RECORD_ARCHIVES.json](RECORD_ARCHIVES.json). Normal and optimized row bytes
differ and are not declared identical. Nonfinite test values use the explicitly
tagged representation described in CONDITIONS; this is not provider telemetry.

The separate saved-only reader checks attempt/call identity, usage coverage and
arithmetic across those rows. It additionally checks the four failed/unavailable
outer-effect plus terminal-journal cases and two actual compiled-core refusal
cases before/after a completed prefix. Each mode rejects four copied changes:
lost completed receipt, false success, lost attempt and changed usage total.
[SAVED_AUDIT.json](SAVED_AUDIT.json) and audit streams/receipts retain the results.
The reader does not import or call the caller or application. Its source and the
test runner are inert `.py.txt` reference data with original local path bindings;
they are not registered executable entry points.

## Requirement-to-current-check crosswalk

| #57 requirement | Current evidence in the selected tests | Remaining gate |
|---|---|---|
| All-attempt accounting, missing usage, costs and subsets | Cost coverage, aggregate-cost, failure-metadata, usage-subset and joint invocation tests; saved rows conserve attempts and reported usage | Values are synthetic. Actual provider stages, model calls occurring inside adapters, every route/phase and acquisition/repair costs need the live shared ledger. |
| Fresh target evidence after model wait | Caller v3 tests reject changed or same-frame post-model evidence and prevent authority escalation | Exact observation/admission adapters and final check-to-input race must be qualified in the chosen live caller/backend. |
| Completed prefix, uncertainty and no blind replay | Dispatch, custody, terminal, retained uncertain-tail JSON and actual compiled-core refusal composition | Admission, release and effect adapters in the core composition are synthetic. No native release bound or physical/semantic effect follows. |
| Preserve completed execution when effect is unknown/failed | Four verify-progress rows keep detached completed execution, confirmed delivery and failed/unavailable effect, including terminal journal failure | A returned result is not durable publication, restart recovery or independent application scoring. |
| Independent effect evidence | Bounded effect-reference tests retain valid reference/digest/scope and reject malformed references | Retrieval, evidence identity, collateral effects and independent task predicates require actual retained application evidence. |
| Matched efficiency and transfer | Caller mechanics and comparison classes are available in current main | This batch runs no cold/warm/invalidation/repair comparison, measures no tokens or GUI latency, and qualifies no second domain. |

**Decision:** reuse the current caller instead of rebuilding the old PR union.
The next composed-path check must connect a selected real task's effect and
model-stage evidence to this ledger, including a changed/unknown case, while
preserving completed input and prohibiting automatic replay. Only after those
mechanics and valid resource conditions hold can a fresh matched comparison
qualify #57. Local method counts and synthetic success labels are not that proof.
