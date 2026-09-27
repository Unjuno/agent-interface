# Issue #3188 — MAP01 entry-gate CI execution

Disposition: PASS_MAP01_ENTRY_GATE_EXECUTION_SCOPED.

## H / T

The single preregistered GitHub Actions dispatch against frozen commit e9198a1c74ef4ca2759e92c4539b10dbe3a20ba8 completed the existing entry-gate workflow. The run executed native generation/audit, then the network-disabled Docker generation and audit in separate invocations. No dispatch retry, source edit, or post-freeze tuning occurred.

## D / observed result

- GitHub run 35529905690, attempt 1, job 106128552535; every step completed successfully.
- Native and container outputs each contain 32 ordered Boolean vectors and five named negative controls. The two raw files are byte-identical with SHA-256 8460a9ca79611929cbd6d2f6930067a06c6f177e7da3287ad07d1b7f483cb324.
- Both candidate-auditor summaries report rows=37 vectors=32 authorize=1 current=HOLD controls=5/5.
- Independent raw reconstruction accepted only the all-true vector (1 AUTHORIZE, 31 HOLD), verified all five named controls as HOLD, and rejected four corruption probes: a vector bit, summary count, frozen source hash, and expected class label.
- Frozen workflow/run/audit source hashes and artifact hashes are recorded in FREEZE.json and SHA256SUMS. Full rendered Actions log and both raw artifacts are retained.

## C / execution boundary

GitHub-hosted Ubuntu 24.04.5 LTS, runner image 20260907.300.1, runner version 2.337.0. Docker command used --network none and python:3.12-slim; the run log resolves that tag to sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9. The workflow used a mutable tag, so the resolved digest is evidence from this one execution, not a pre-pinned immutable image reference. No model, game, GUI, X11, native input, recovery execution, or production authority was exercised. This CI container run does not establish that local Docker Desktop works.

## U / limits

This is only a finite readiness-gate truth table and artifact/audit boundary. It does not establish MAP01 recovery efficacy, model quality, or live runtime safety. Current snapshot remains HOLD; this result grants no execution/recovery authority.