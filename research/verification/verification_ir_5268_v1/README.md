# Verification IR v0.1 — Issue #5268

**Scoped result:** `PASS_IR_ORACLE_FINITE_SCOPED` for one frozen synthetic
Agent Action corpus. This is a typed representation/oracle check, not an
integrated verifier, runtime change, or action authorization.

## Result at a glance

- 10/10 action fixtures matched the independent literal oracle.
- 32 checks retained exact primitive, subject, criticality, evidence role,
  verifier class, dependencies, deadline slot, budget class, and fallback.
- 0 oracle disagreements; 0 authority fields in any emitted IR.
- 8/8 copied-result corruption controls rejected, including mandatory-check
  omission, criticality downgrade, subject/role/dependency changes, unknown
  primitive, authority injection, and suppression of the unknown marker.
- The candidate emitted no PASS/FAIL action verdict. Unsupported evidence stays
  `unknown_check_required=true` with `META.UNKNOWN_REQUIRED`.

See [the full report](REPORT.md), frozen design [PLAN.md](PLAN.md),
[raw formal output](FORMAL-01.json), [independent audit](AUDIT-01.json), and
[source freeze](FREEZE.json).

## Reproduction

The formal output in this directory is the sole allocation and must not be
overwritten or rerun. To reproduce in a fresh, disposable copy of this study,
use the pinned image and run the frozen command in `FREEZE.json`; then run the
auditor once with `--out AUDIT-01.json`. The runner refuses an existing formal
output, and the auditor refuses an existing audit output. The seven standard
library unit tests are non-formal construction checks.

The raw-only auditor imports no candidate or formal runner. Its independent
oracle and fixtures were authored by the same researcher; this is code-path
separation, not independent-human review.

## Scope boundary

This corpus says only that this representation preserves these hand-authored
cases. It does not establish ontology completeness, detector recall, the
correctness of any real verifier, freshness/authenticity of evidence, a
production policy, latency or efficiency benefit, task success, or transfer to
Code Change/RAG Claim. #5269 and #5275 remain untested and should wait for review
and an accepted v0.1 boundary.
