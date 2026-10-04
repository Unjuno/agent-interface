# #6509: actual process-exit and disk-prefix construction boundary

Worker 01a0ff58-6178-7ea1-a6d5-cf09260b91e3, FINAL-v5.
Base main f1416985d4ff9ce5bbf9f0f4be1be3d0ee669549.
This is a new ordinary construction boundary, not a retry of the original T0.

The prior 45-row T0 and its independent scope check established authored logical dispositions. They explicitly did not test disk journals or actual process recovery. This package tests that residual using actual native Windows file writes, flush/fsync, abrupt child exit and two distinct read-only recovery children.

- H: source-current, complete newline-terminated receipt prefixes can be reconstructed after process exit without accepting partial-positive, torn, stale-generation or duplicated evidence as complete.
- T: freeze nine cases and all six source files before a single boundary matrix. Each case gets one fresh writer and two independent recovery process invocations. No rerun on unexpected exit. Preserve the journal, optional cached marker, captured stdout/stderr, exits and UTC boundaries. Audit retained bytes separately without importing producer/recovery. The earlier eight tests are engineering construction checks.
- D: PASS_PROCESS_EXIT_BOUNDARY_SCOPED only if all nine exact journal prefixes, all 27 exits, both recovery outputs, missing/completed check sets and declared dispositions match; six raw corruption controls must fail. Expected outcomes: three COMPLETE_VERDICT, one COUNTEREXAMPLE and five PARTIAL_UNKNOWN. Cached-marker negative control must expose two false complete labels. Otherwise retain FAIL or STOP; do not alter the cases.
- C: always-UNKNOWN is safe and sufficient if no positive reuse is needed. Ordinary validated journal replay may be sufficient; no new runtime mechanism is proposed. Cached-verdict trust is an intentionally insufficient control, not the current runtime. Metadata availability is distinct from real latency or consumer effects.
- U: the check values, generations and scope are synthetic. The observed property is process-exit visibility on this Windows filesystem, not power-loss durability, directory durability, arbitrary torn-write behavior, concurrent writers, exactly-once consumer effects, semantic verifier truth, GUI/input release, authority or performance. An os._exit cut is planned process termination, not a real machine failure. No platform transfer is claimed.

Use native CPython because the question is this Windows process/filesystem boundary. No WSLc is installed in this worker environment; no shared Docker/WSLc/GUI/GPU or model is invoked. Children run serially, outputs are small, and the parent timeout is 15 s per child. That timeout bounds this harness's own children and is not proof of host memory enforcement.

Receipts have three ordered mandatory checks: identity, freshness, effect. Only identity/effect false are independently decisive negatives in this declared synthetic contract. A false freshness without a decisive negative remains UNKNOWN. All labels are descriptive and never grant input authority. No external consumer operation is performed.

Cases c01/c02/c03 stop after 1/2/3 flushed receipts; c04 stops before publishing the cached marker; c05 stops after it; c06 retains a flushed partial third JSON line; c07 stops with an identity-negative receipt; c08 changes current generation after writing three receipts/marker; c09 appends a duplicate fourth receipt after writing the marker. Only complete newline-terminated records contribute; complete-record corruption, stale scope/generation, invalid types/order or duplicate check refuse all reuse.

The eight test-first cases initially produced four intended assertion failures with the unimplemented conservative stub; the implemented reconstructor passes 8/8. These checks do not consume the new nine-case matrix and do not replay historical formal allocations.

Variable definitions: sequence is a positive integer, dimensionless record order; generation is a positive integer synthetic evidence version, dimensionless; value is a boolean authored check result, dimensionless; scope/check/disposition are finite nonphysical identifiers; completed/missing are lists of check names; byte sizes and SHA256 identify retained files; UTC start/end are actual observed timestamps in seconds with no performance interpretation. No theoretical or measured speedup is computed.
