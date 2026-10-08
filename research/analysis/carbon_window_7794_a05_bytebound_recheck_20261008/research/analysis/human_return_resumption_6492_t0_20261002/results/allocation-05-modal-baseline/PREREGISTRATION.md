# Issue #6492 — immediate-modal baseline successor allocation 05

Allocation 04 is preserved as `STOP_INFRASTRUCTURE_BEFORE_CONTAINER`: Docker
CLI could not open its incorrectly container-relative CID-file path, so the
Python candidate was invoked 0 times and no container was created. Allocation
05 is a separately frozen launcher successor, not a retry of a candidate
result. It reuses the same six immediate-modal rows and exact candidate/auditor
source hashes; the only launcher correction is a host-absolute `--cidfile`
path inside the already-created host output directory. Allocation 04 remains
unchanged.

This remains distinct from PR #6499: only its missing `immediate_modal` arm is
tested; the `timing_only`, `preserved_view`, and `optional_cue` rows are not
emitted or re-run.

H/T/D/C/U and all seven corruption criteria are unchanged from
`../allocation-04-modal-baseline/PREREGISTRATION.md`. Candidate emits six rows;
one independent audit invocation checks the baseline and all seven frozen
mutations. No people, GUI, model, personal data or real effects.

Current main at freeze is `a7817597b8405f9b7581820fe79c9242a5f65255`.
Immediately before candidate launch, fetch and fast-forward latest main only
after confirming any advances are disjoint from this package and governing
documents. Recheck Issue #6492 is open, PR #6499 still covers only its original
three arms, and there is no new immediate-modal successor. Source hashes must
match and both output paths must be absent. Candidate maximum=1, auditor
maximum=1, retries=0. Any Docker CLI failure, nonzero process exit or missing
output terminally stops allocation 05.

Container runtime: pinned `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`,
linux/arm64, OrbStack 29.4.0, network none, separate ephemeral containers,
source/root read-only and output separately writable, requested 1 CPU, 512 MiB,
pids 64, user 501:20, no GPU. Resource enforcement is not inferred from these
configuration requests.
