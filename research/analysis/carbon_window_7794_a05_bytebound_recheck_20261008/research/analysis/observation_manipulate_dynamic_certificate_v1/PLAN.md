# #1904 state-conditioned MANIPULATE_TO decision certificates

H: for fixed MANIPULATE_TO branch truth tables, a minimum-cardinality certificate of the current branch decision can be strictly smaller than the whole phase-level support union while remaining exactly safe.

T: source-first. Construction only six hand-selected current states and16 masks/state. Formal, only after freeze, derives certificates for all48 current states and evaluates all768 transitions. Candidate chooses minimum cardinality with deterministic T<D<E<S tie-break. Independent audit re-derives masks without importing candidate code.

D: certificate validity/minimality errors0; dynamic/phase-union/global false suppressions0; dynamic false-forwards < phase-union < global; dynamic safe suppressions > phase-union; strict narrowing exists; exact certificate/audit/source integrity pass.

C: cardinality-minimal support need not minimize actual observation cost; equal-cardinality certificates can differ in capture expense.

U: synthetic Boolean branch semantics only; no GUI/model/token/latency/runtime claim.
