# Role-skill lifecycle amortization (Issue #5008)

This additive successor tests one part of #4916's reload-vs-reuse idea against
the exact retained seed-3788 package. It is deliberately framework-independent:
standard-library JSON/digest/shape validation and a pure-Python float32 scorer
are used because the predecessor's pinned PyTorch image is not present locally.
The construction gate compares the scorer against every one of the 12,288
retained expected predictions before any timing block can run.

The frozen formal experiment executes 15 paired blocks of a deterministic
1,000-request A/B/C schedule. One arm reloads, validates, and constructs the
selected role on every request; the other loads, validates, and constructs all
roles once, including that setup in its lifetime cost. Both score the same
vectors. A separate auditor recomputes predictions without importing the
candidate implementation, checks hashes/order/paired outputs, and applies
corruption controls.

The evidence answers only whether this exact synthetic package's file/JSON/
validation/construction lifecycle amortizes under this pure-Python scorer and
cached container. It does not measure PyTorch, the original framework runtime,
real request distributions, task success, or product latency. See `FREEZE.json`
for source/input hashes, exact Docker commands, gates, and no-retry policy.

## Allocation 01 — construction STOP

The frozen construction invocation stopped before loading the fixture because
the test module eagerly evaluated an invalid fallback path under its `/src`
container mount (`IndexError` in `Path.parents[1]`). The machine-readable
receipt is `results/construction-01/construction.json`; the exact STOP and
invocation details are in `FORMAL_FAILURE.md`. No parity row or formal timing
row was executed. Allocation 01 is consumed and must not be retried; any code
correction belongs in a separately frozen successor allocation.
