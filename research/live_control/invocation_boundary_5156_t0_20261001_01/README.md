# #5156 invocation-boundary T0

This host-only experiment tests whether a run-specific ID and per-invocation
artifact namespace prevent multiple STOP/raw records under one allocation ID
from being conflated. It is motivated by the Allocation 04 cross-record
reconciliation; it does not retroactively assign IDs to those historical files.

H: a unique invocation ID, used on the invocation manifest/raw rows and in the
artifact directory, makes identity checkable; absent or conflicting IDs must
stop rather than infer a run count.

T: one candidate invocation classifies eight frozen fixtures, then a separately
implemented raw-only auditor reconstructs each decision and checks five frozen
negative/corruption conditions.

D: see `RESULT.md`; the maximum decision is provenance-contract scoped.

C: no Docker/X11 was run because this finite standard-library contract required
no external runtime and #5085 did not assign this experiment a shared container
slot. No model, GPU, GUI, input, or network.

U: this does not resolve Allocation 04's unknown invocation history or prove
any X11/key-up behavior. A later formal run still needs an explicit exact lease.
