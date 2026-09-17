# USEFUL-CONTROL-PROVENANCE-COMPOSITION-FORMAL-20260917-001

BASE: 592427d8f70efafed5819acec123f3fd0efa485b
PARENT: #963 merged composition

H: Exact merged composition preserves parent occupancy and matches an independently authored effect-role/provenance oracle on fresh valid/mixed data, while malformed cross-gate data fails closed according to frozen gate precedence.

T: Source-first standard-library container formal. Fresh valid seed 96320260917011 / 100000 cases; malformed seed 96320260917012 / 50000 cases. Small integer time domain permits independent discrete-set occupancy oracle. Exactly one formal invocation after Git publication/readback and ownership reread; reruns/replacements/tuning0.

D: PASS iff 100000/100000 valid cases match aggregate four occupancy bounds, per-actuation bounds and six effect buckets; 50000/50000 malformed/multi-fault datasets match exact gate/bucket precedence; boundary controls pass; side-effect counts0; source/result/audit integrity passes.

C: Parent occupancy delegation structurally favors arithmetic agreement, so the formal oracle must not call parent occupancy helpers. Gate order is policy, not universal truth.

U: Synthetic same-process integer-time evidence only. No X11/MAP01/distributed exactly-once/production claim.
