# Result

The exact PR #7378 parent source (`fbed929f629dabaa9ae752019d0ee7151d4d2298`)
fails the new cleanup-overlap regression: `ordinary_release_candidate` remains
true when a verified cleanup release timestamp is inside the explicit `up`
bracket. The candidate demotes that row and refuses owner-transition
verification. A cleanup timestamp outside the bracket keeps the positive
ordinary-release result; unavailable cleanup records fail closed.

The current-v39 backend test module passed 21/21 tests in WSLc. Combined with
the adjacent `input_transition_owner_v3` suite, 29/29 passed. The first auditor
reported seven string checks on retained output, but review found that it did
not reject a contradictory failure summary or compare an exit receipt; its raw
output is preserved as superseded. The corrected host-side auditor requires
one terminal unittest summary and matching exit receipts; it passes 9/9 checks,
and its five mutation tests pass. The inherited backend suite includes
synthetic base-class tests; this result does not claim every inherited case is
reachable through an admitted v39 program. WSLc emitted its known warning
that swap limits are unsupported; accepted memory limits do not establish swap
isolation.

This establishes a deterministic telemetry-classification boundary in the
adapter. It does not establish owner-thread queue scheduling, live input or
physical release timing, task effect, product reliability, or any model/GPU
claim. No live allocation was invoked or retried.
