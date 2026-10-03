# Rescue review: historical three-boundary kernel combination

Original PR #6871, source `0652db3b821152cc3912dba33ea1da1956b8206c`,
contains 58 retained files and a 57-entry SHA-256 manifest. Every original file
is copied byte-identically; all 57 hashes match. Original README, freeze,
execution receipts, publication/redaction limits and mutation failures remain
unchanged. This qualification is additive and is not in the historical manifest.

Independent local rescue checks on main
`30cd9cd27e75ceed6f1cfd6d5b518b87581478f6`:

- Read-only `oracle.audit()` exactly reproduces both saved audit JSON objects.
  Baseline and combined each contain 2916 rows. Baseline has 2908 authored
  contract-mismatched rows; combined has zero. `PASS_RAW_COVERAGE` alone is not
  a correctness PASS for baseline; the mismatch counter must also be inspected.
- Original raw-data oracle controls pass 10/10 in both normal and optimized
  Python modes. They mutate in-memory copies only and import no producer/runtime.
- No original probe, candidate matrix, mutation producer or native backend is
  re-executed. No formal allocation or input authority is created.

The retained combined kernel snapshot is NOT byte-identical to today's kernel:
current `lifecycle.py` has six additional lines, and current kernel contains
additional execution/cancellation regression files and README. This archival
delivery does not restore any snapshot into runtime, and does not reuse the old
combination PASS as a current-runtime combination certificate. Original proposed
tree/main review state and committee discussion remain historical, not fabricated
approvals for this rescue. Source PRs #6853/#6859/#6861 are not merged or modified
by this evidence-only delivery.

**H:** the historical exact three-guard conjunction satisfied its sequential
inert authored contract. **T:** original baseline/combined matrix and independent
oracle; rescue only rechecks immutable saved outputs and corruption controls.
**D:** PASS_ARCHIVAL_INTEGRITY_AND_SAVED_ORACLE; current-runtime compatibility
NOT_ESTABLISHED_BY_THIS_ARCHIVE. **C:** authored matrix failure counts are not
production prevalence; unchanged saved output does not prove a changed kernel.
**U:** concurrency, live release, clock domains, GUI effect and performance are
not established. Earlier overwritten/redacted/private evidence limits are not
repaired or hidden by this publication.

All 38 Analysis Index run steps are separately checked locally before push;
this does not run the preserved matrix. OrbStack container availability was
already STOP_RUNTIME_UNAVAILABLE during the preceding rescue, so no shared
runtime reset, image pull or container experiment is attempted here.

User-authorized old-branch rescue proceeds through an additive PR under normal
GitHub branch rules. Full original source tip remains recoverable in an annotated
archive tag before the unchanged remote ref is retired. No committee vote is
claimed or copied.
