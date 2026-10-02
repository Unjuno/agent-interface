# Shared public caller: delivered-capture invalidation

Concrete common-assistance correctness blocker in #57/#56/#2789, following
#6323/#6330. The original #6323 keeper advanced local source state from a nested
returned capture even when presentation withheld that image. No actual later
reading/input used its affected final capture; its frozen source/results remain
unchanged. This successor uses one shared DeliveredCapture state for ordinary and
compact presentation and tests it in the standard native protocol suite.

The state clears its previous candidate before every attempted acceptance. It
admits only one explicit selected source: direct observation ID, post-dispatch
observation ID, or execution observation index. The presented PNG bytes/hash/path/
capture timestamp must match the selected native artifact. Returned nested captures
under inspection error are refused. Omitted, withheld, malformed and mismatched
presentations clear the prior image; there is no older-image fallback. Selection
returns copies, grants no input/freshness authority and does not acknowledge redraw.
It verifies response inclusion, not provider delivery or primary-model ingestion.
A downstream pixel reader still verifies stored bytes and decodes the PNG.

The additive keeper replaces all three capture updates (observe, dispatch,
review_target). It increments its local sequence only for admitted presentation,
clears last_native otherwise, and refuses read_cells without a delivered candidate.
A target review with unmatched/unconfirmed capture cannot bypass that gate; its
committed binding revision remains untouched. The unchanged pixel read function
is copied from the predecessor. The new helper import occurs before GUI allocation;
a successor archive containing it must be built/pinned before any live allocation.
No fresh live allocation was made for this correction; it is not a frozen formal
comparison protocol and has no latency/token/effect result of its own.

Ten original retained presentations were replayed read-only from #6323: all
selected native identities match; plain final withheld capture now clears state.
The compact final image still contains stale modal pixels and is accepted only as
an identity-matched response image, never semantic completion. This unresolved
redraw limit remains; no state checker can infer pixels reflect application intent.
The tests cover plain/compact equivalence, candidate copying, omission/withholding,
wrong bytes/hash/path/ID, nested capture error, ambiguous selectors, boolean index
and malformed response, with explicit previous-candidate invalidation.

Initial test construction failed because the new module did not exist yet. After
implementation, five regression methods pass normally and under -O; complete
native logs/commands are retained below. Actual provider usage/cost and performance
improvement are not established. Existing frozen evidence is not relabeled.

Next #57 gate: strongest ordinary conditional composition and integrated continuation
must use equivalent read assistance/safety/timing, then freeze the full cold/warm/
changed/repair/reuse allocation and economic thresholds before execution. This
change addresses the documented invalidation blocker; it does not substitute
these five unit methods for that end-to-end comparison.
