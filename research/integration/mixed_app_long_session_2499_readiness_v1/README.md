# Fail-closed readiness guard for #2937

The guard rejects missing, ambiguous, or auxiliary-only identity before any
geometry/focus/input operation. It is additive and does not claim a formal
mixed-app session.
