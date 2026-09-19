# Portable runtime v0.1 repair plan

Changed conditions from the retained v0 first result:

1. require exactly one `release_all`, and require it to be the final operation;
2. add an exact provider-usage ledger that cannot relabel byte proxies as tokens;
3. import one already-retained golden runtime aggregate usage record as a ledger
   conformance fixture only. Do not rerun that model allocation.

Run the complete deterministic test suite, then one new `portable-runtime-v01-20260915-01`
offline corpus under the repaired contract. No model/GUI/OS input/network.

PASS only if the v0 posthoc counterexample is rejected, all old valid corpus cases
still round-trip, the retained exact usage fixture validates, and token comparison
eligibility fails when exact-provider/equal-correctness/matched-task conditions are
not met.
