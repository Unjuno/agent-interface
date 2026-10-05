# Issue #7487 T0 result — PASS_METHOD_SCOPED, host-only

At 2026-10-04 06:28 UTC, the frozen candidate produced 20 synthetic
renderings from five stipulated source-ledger cases across 300/1500 ms display
delay and chronological-summary/source-bound-receipt formats. The separate
raw-only auditor reconstructed every row with zero mismatches, rejected all
six effective field/order/link mutations, and verified that unknown/conflicting
provenance stayed `UNKNOWN`.

This meets only the Issue's `PASS_METHOD_SCOPED` T0 gate. It establishes that
this fixture renderer/auditor preserves its stipulated source relations and
presentation invariants. It does not test whether people notice, understand, or
use those relations; it cannot support the Issue's human hypothesis.

## Deviations and limits

OrbStack inventory stopped before candidate launch because a read-only image
listing failed on a cached containerd blob with `operation not supported`.
No image acquisition, daemon repair, or retry occurred. The finite
standard-library run was therefore host-only; this is not container evidence,
isolation evidence, or proof of resource controls. One incorrectly rooted
construction-test command failed to import the local auditor module; the
package-directory test passed before the frozen formal candidate/auditor pair.

No participant, GUI, application, model, causal-source discovery, actual
display delay, attribution accuracy, confidence, blame, trust, authorization,
safe retry, task completion, runtime integration, or product outcome was
measured. T1 remains unauthorized and requires separate ethics/consent approval.
No result beyond this finite synthetic method scope is claimed.
