# Active-turn request ordering A03

## H / T / D / C / U

- **H:** Codex CLI 0.160.0 accepts an `ExternalMessage` on the still-running turn but does not issue the updated Responses request until the original mock response completes.
- **T:** Freeze the probe, test, retained seq=200 PNG, CLI version, and 2.0-second pending window. Start a turn against a loopback-only Responses mock whose first request blocks. After the actual `turn/start` ExternalMessage reply, wait exactly 2.0 seconds for request 2 while request 1 remains unanswered, then release request 1. Invoke the candidate once.
- **D:** `SECOND_REQUEST_WHILE_INITIAL_PENDING` means request 2 arrived before the first response was written. `SECOND_REQUEST_AFTER_INITIAL_COMPLETION` means it arrived after the first response write completed. Missing timestamps, absent request, incorrect turn ID/status, missing exact text/image, server errors, or incomplete turn are retained as STOP/failed gate. No retries or negative-control variant are authorized in this one-shot.
- **C:** This is a local Codex App Server protocol test using an ephemeral loopback mock and temporary `CODEX_HOME`. It performs no model inference and contacts no game, GUI, or input backend. The PNG is a retained historical frame used only to verify request serialization.
- **U:** The ordering result applies only to this CLI version and mock protocol. It does not establish model comprehension, changed planning, cancellation/release, V39 integration, useful feedback, recovery, ammo/progress, terminal outcome, or Issue #59's fresh live threat-exposure gate. The private live lane remains unassigned.

## Relation to existing protocol evidence

Open PR #7951's A02 retained same-turn-ID and image-serialization checks but did not retain timestamps bracketing the first mock response. A03 isolates that remaining transport-order question; it does not replace A02 or upgrade its scope.

## Result

The single frozen candidate completed with exit 0. The ExternalMessage response returned the original turn ID with status `inProgress`. No second Responses request arrived during the 2.0-second pending window. After the first mock response finished writing, request 2 arrived 15.3 ms later and contained the exact observation text and the 149,687-byte PNG (SHA-256 `0e6b6570944c3e0c60ca3eff5e84bc9371187cd8cea6a7d237e66cc06645483c`). The turn completed and the mock server recorded no errors.

This is one loopback observation on CLI 0.160.0. It supports a queued-after-response interpretation for this setup; it does not show how a model would respond to the observation or whether that delay is acceptable for live control.

## Verification

- `python3 -m unittest -v test_probe` — 6 tests pass.
- `python3 -m py_compile probe.py test_probe.py audit_result.py` — pass.
- `python3 audit_result.py` — `PASS_RETAINED_PROTOCOL_ORDERING_RESULT`.
- `git diff --check` — pass.

The candidate command, raw stdout/stderr, exit code, unit-test output, and audit output are retained in `results/`; `SHA256SUMS` binds the package and evidence files.

## Frozen candidate

See `FROZEN.json` for base commit, exact command, candidate/test/fixture hashes, one-shot limit, timeout, and decision labels. Candidate stdout, stderr, and exit status are retained under `results/`.
