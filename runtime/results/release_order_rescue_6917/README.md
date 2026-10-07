# Rescue of #6917 aggregate release-order counterexamples

Original source `93dd008c3a90a5e255a2683d8373582bec48b320`, PR #6917,
Issue #57 / #5156. Preserve all 41 original packet files and the consumed
candidate/auditor 1/1, zero-retry first outcome. No production change or promotion.

`python -B runtime/results/release_order_rescue_6917/test_archive.py -v`
checks complete40-entry manifest, then original full 36-row raw-only audit and
all twelve corruption controls on a fresh receipt. Entire audit JSON must equal
historical JSON: integrity PASS but **FAIL_TERMINAL_RELEASE_IDENTIFIABILITY**.
Six identical complete projection classes contain opposite terminal states;
the kernel-report and end-floor comparators each disagree with twelve modeled
terminal predicates, while the extra ordered witness disagrees with zero.
These are finite modeled alternatives, not actual physical-backend failure rates.

The original read-only Git checker also rechecks eighteen frozen files against
prospective committed bytes, eight primary/construction source Git blobs, public
capture stream hashes/derivations, original invocation counts and collision pair.
Fresh readback equals historical public scope except fresh UTC and the explicit
private-original count: zero private captures checked here vs three on the author
host. Private captures are not claimed verified or reconstructed. Assert-based
readback/control-effectiveness assertions are run without `-O`.

The collision does not establish reachable bad histories under a stronger real
backend terminal-release contract. The end-floor alternative refuses safe modeled
bookkeeping tails; it is not adopted as a blanket repair. No live input/backend,
clock authentication, arbitrary actor/concurrency, application effect, model,
latency, token saving or production adoption claim follows. No primary matrix,
run_once, container/VM, formal/live allocation or other worker resource is replayed.
