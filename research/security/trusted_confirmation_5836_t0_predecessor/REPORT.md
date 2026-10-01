# Issue #5836 T0 first outcome — preserved STOP

Allocation `trusted-confirmation-5836-t0-20261001-01`, frozen against main `49db21e330768800e8b3486203b70306f4e402f6`.

## H/T/D/C/U

- **H:** A separate request-bound single-use trusted confirmation channel rejects agent/app forgery, replay, request substitution, revocation and ambiguous-delivery retry while preserving matched approval and denial.
- **T:** One CPU-only Docker Desktop candidate run and one separate raw-only audit, 10 fixed synthetic scenarios, three comparison arms. No model, GUI, person, credential, payment, privileged action, or real effect.
- **D:** The preregistered `PASS_METHOD_SCOPED` gate was not met. The raw candidate grants the trusted arm in its `replay_receipt` row, exposing a missing nonce-consumption state. Do not interpret this raw failure as an externally realistic exploit.
- **C:** Simulated channel provenance may be an invalid trust abstraction; broker-bound confirmation may not need a rich receipt.
- **U:** Synthetic-only; no OS/hardware trusted path or human comprehension evidence.

## Executed environment and immutable first outputs

- Docker Desktop Engine 29.8.0, context `desktop-linux`, Linux amd64.
- Image `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; inspected image ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Both commands used `--network none --read-only --cpus=1 --memory=256m --pids-limit=64`, a read-only source mount, and a separate output mount. Candidate exited 0. Independent auditor ran once and returned `FAIL_AUDIT` (nonzero).
- Candidate source SHA-256: `048c07c6fffa3065c9df8392041a80a1a9d3fa3a857f59a3fe91f3aefda6ef33`.
- Auditor source SHA-256: `168a6de222095bec8de77351fe42474abdab773ca04e65534bb7c2164e1319b5`.
- Frozen plan SHA-256: `c795e9fd4d4f71a97cf538502d83c7ed57228b173e2ae35d474bb45d9dce250c`.
- Raw candidate JSON SHA-256: `4f9fe57247c696fffc5a829539173d58b80d0d3d556103ca71d58856d2795591`.
- Raw auditor stdout is retained verbatim in `results/AUDIT_STDOUT.json`; five of five planted mutations were rejected.

## Audit limitation discovered after the one-shot audit

The first auditor's comparison-arm oracle was wrong: it expected a *request-bound* but replayable receipt to authorize target swap, principal mismatch, and revocation cases. A request-bound receipt should reject those changes even if replay remains possible. Therefore the first auditor's overall `FAIL_AUDIT` is preserved but is **not a valid adjudication of all comparison-arm cases**. The raw row independently shows the candidate trusted arm authorized the replay case, but no corrected formal conclusion is assigned to this consumed allocation.

Disposition: `STOP_AUDIT_ORACLE_INVALID; CANDIDATE_REPLAY_STATE_DEFECT_OBSERVED; NOT_METHOD_PASS`. Candidate=1, auditor=1, retries=0. No rerun, source replacement, or relabeling of these bytes. Any corrected test must use a distinct successor allocation, corrected baseline oracle, and an explicit consumed-nonce state machine.
