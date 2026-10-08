# Issue #6492 T0 — successor allocation 03

Allocations 01 and 02 remain immutable pre-candidate STOPs; each has
candidate=0, auditor=0, retries=0. Allocation 03 is independently named and
uses a separate output namespace. It reuses the frozen 24-row fixture and
candidate byte-for-byte, verified with the two preserved source manifests.
The successor auditor wrapper runs the clean raw reconstruction and all six
corruption controls inside its single invocation, without importing candidate
code.

H/T/D/C/U and all four-arm/six-scenario design constraints are unchanged from
the root `PREREGISTRATION.md`. No participants, GUI, model, personal data,
external interaction, or effect. `PASS_METHOD_SCOPED` is limited to the
authored synthetic method fixture.

## Current-main start gate

Freeze base and branch head: `95431dc7537e55782dd3997fe04b55a729b91fe6`.
Immediately before launch, fetch the newest `origin/main`. Fast-forward this
branch to that exact SHA. Disjoint main advances are admissible only when all
changed paths are outside this package and outside the canonical current-goal,
roadmap, worker, failure-classification and Issue-index files. Record every
intervening commit/path in `RUN.json`. Any overlap, conflict, relevant-goal
change, Issue #6492 ownership/result change, source/image hash mismatch, or
pre-existing output is a STOP before candidate. Revalidate frozen hashes after
the fast-forward. This keeps current main integrated without converting an
unrelated, path-disjoint merge into repeated allocation STOPs.

## Execution contract

Candidate maximum=1; independent auditor maximum=1; retries=0. Pinned
`python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`
(`linux/arm64`), OrbStack Engine 29.4.0, network none, separate ephemeral
containers, source/root read-only, separate output mounts, requested 1 CPU,
512 MiB, pids 64, UID:GID 501:20, no GPU. Settings are requests only; no
resource enforcement claim absent readback.
