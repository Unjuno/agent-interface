# Issue #6492 T0 — successor allocation 02

Allocation 01 is preserved as `STOP_BEFORE_CANDIDATE_MAIN_ADVANCED`; it used
zero candidate/auditor invocations. Allocation 02 is a new, separately frozen
current-main allocation, not a retry of a candidate result. It reuses the
identical method package and fixture byte-for-byte, verified against the
original `FROZEN_SHA256SUMS`. The distinct output namespace is
`results/allocation-02/`.

The successor-only root `audit_controls.py` runs the clean 24-row reconstruction
and all six frozen output corruptions in the one formal auditor process. It
imports only the independent `audit.py` verifier, never `candidate.py`; its
bytes and test are listed in this allocation's own source manifest. This
closes the control-gate ambiguity without changing allocation 01's frozen
source or evidence.

H/T/D/C/U and all scenario, matched-arm, mutation, and stopping criteria are
unchanged from the immutable root `PREREGISTRATION.md`. It remains method-only:
six synthetic scenarios × four arms = 24 rows, no humans, GUI, model, private
data or actual effect. A successful audit can only produce
`PASS_METHOD_SCOPED` for these authored fixtures.

Source base and branch HEAD at this freeze:
`e97d21bb6142b3ed0be00744671d3b16f5cde5bb`. The current-main equality gate is
rechecked immediately before candidate invocation. Candidate=1 maximum,
independent auditor=1 maximum, retries=0; a main advance, hash mismatch,
pre-existing output, missing output or nonzero exit terminates this allocation.

Runtime remains the cached digest-pinned Python 3.12 slim `linux/arm64` image,
OrbStack Engine 29.4.0, network disabled, separate short-lived candidate and
auditor containers, read-only source/root, separate writable output, requested
1 CPU, 512 MiB, pids 64, user 501:20, no GPU. These are requested settings;
resource enforcement is not inferred without runtime readback.
