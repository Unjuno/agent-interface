# Issue #6278 T0 — exact-effect and temporal eligibility boundary

## H / T / D / C / U

**H (bounded):** A nominal capability edge is not a buffer unless it is independently effect-qualified, authorized, available after the modeled dependency loss, and can complete before the obligation deadline. This T0 tests that eligibility boundary on a deterministic finite fixture; it does not test the comparative portfolio claim.

**T:** Apply one deterministic greedy allocation to an authored finite fixture with route/obligation eligibility, dependency loss, release time, readiness delay, effect time, deadline, and capacity. Compare candidate rows against an independently written verifier; exercise boundary controls. This package intentionally does **not** claim to complete Issue #6278's optimized multi-topology portfolio comparison or establish a GUI benefit.

**D:** Immutable fixture; candidate raw JSON; independently recomputed audit JSON; source/image identities; exact invocation count. No model, GUI, external service, or user data.

**C:** A task counts only when its edge is qualified, authorization matches, the route survives the fault, capacity is available, and completion is no later than deadline. Missing or partial effects are not coverage. The universal-route dominance control must tie or dominate. Any invented edge, late completion, or unauthorized admission is rejected.

**U:** Synthetic method boundary only. Portfolio-design optimality, route discovery, real task/fault distribution, GUI effects, and human/agent benefit remain untested. T1 eligibility is not established.

## Construction fixture

Eight offered tasks exercise exact, partial, unauthorized, and deadline-expired effects. Three routes include an apparent overlap route, a specialized route and a universal comparator. Scenarios include no fault, loss of a shared dependency, and reconfiguration beyond the deadline. The independent auditor recomputes the deterministic greedy choice with separately written control flow; it does not import candidate code. This is not an exhaustive optimizer and does not establish the temporal-buffering or route-portfolio hypothesis.

Run with `python3 candidate.py --out raw.json` then `python3 audit.py raw.json audit.json`. These are one-shot package commands; do not rerun after a formal allocation. `python3 -m unittest -v` is construction-only.
