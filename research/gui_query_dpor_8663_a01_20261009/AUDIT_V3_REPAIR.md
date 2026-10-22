# Auditor v2 verdict and v3 repair

The candidate raw result remains unchanged. Auditor v2 emitted `FAIL_AUDIT` because its validation compared an unordered dependency-claim collection as an ordered list and applied the true-commutativity check to deliberately under-dependent mutation controls. The independent reconstruction showed the proposed `predicate_dpor` claims match as sets and every declared-independent pair commutes; the false positives came from checking the mutants as if they were the proposed relation.

`audit_v3.py` normalizes claim rows before comparison and applies the commutativity requirement only to the proposed predicate-aware relation. It still requires each under-dependency mutant to omit an oracle outcome, so mutation sensitivity remains checked. It reads the frozen raw result only and imports no candidate code. No candidate rerun occurred.
