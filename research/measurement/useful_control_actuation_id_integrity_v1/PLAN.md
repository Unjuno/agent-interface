# Useful-control actuation ID integrity v1 — construction

H: Holding merged #941 interval/release/authority/effect semantics fixed, causal lineage IDs must be runtime-valid: every actuation ID is a nonblank string; effect IDs are either the reserved `None` unbound sentinel or a nonblank string. Python type hints alone are not authority.

T: Pure standard-library/container construction. Reproduce predecessor fail-open for `None`, blank/whitespace, numeric, bool and bytes actuation IDs; then apply only an ID-integrity adapter. Fixed valid/malformed controls, 100,000 seeded identity cases against an independent oracle, and 50,000 valid mixed traces. No #946/#950/#869 allocation is touched.

D: Construction passes only if malformed actuation IDs reject, malformed effect IDs never bind, `None` remains unbound-only, valid Unicode/nonblank IDs retain exact predecessor semantics, and valid-trace occupancy/effect outputs are unchanged except a zero `invalid_identity` bucket.

C: A future typed serialization boundary may guarantee this earlier; whitespace/case canonicalization would be a different mechanism and is excluded.

U: Synthetic Python object evidence only; no live transport/authentication/X11/MAP01/production claim. Formal authorization is false.