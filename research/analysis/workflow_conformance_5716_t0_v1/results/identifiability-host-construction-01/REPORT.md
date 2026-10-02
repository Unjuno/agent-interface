# Issue 5716 host construction result

Allocation: `5716-TELEMETRY-IDENTIFIABILITY-HOST-CONSTRUCTION-20261001-01`

## Execution

- Host: Windows, Python 3.12.10; no network, GUI, model, application, or external service.
- Candidate invocation: 1; exit 0.
- Candidate source SHA-256: `dabfcb29fc7a0ced4d4dcb2ffb153354ac2b1c87e1b5154d542a72d834b2e907`.
- Complete candidate program SHA-256: `abd83943118f1496f3c946fa660adc9060800776e903acc47181d691d509e494`.
- Candidate raw: 665 bytes; SHA-256 `89a64b887353d6448acdd09fcd6719613fbf1abee7cdf6f44b4d0b5a26f72ed9`.
- Separate raw-only auditor invocation: 1; exit 0; four rows, errors `[]`. Two later post-hoc raw-only audits matched the exact candidate raw SHA and checked exact fixture values; no candidate rerun. One strict audit uses the packaged `audit.py` source (SHA-256 `1529d6ab32989ecc751a4a7a1710960b148f02b30b86bcc2ae0dae05ad49e291`) and reports `PASS_IDENTIFIABILITY_CONSTRUCTION`.
- Docker Desktop context `desktop-linux`: read-only version handshake did not respond. Docker/image/container invocations: 0.

## Result

The exact same release-gap projection produced `UNKNOWN_TELEMETRY` in both hidden-truth worlds. Complete-channel controls produced `CONFIRMED_COMPLETE` and `CONFIRMED_OMISSION` as preregistered. Disposition: `PASS_IDENTIFIABILITY_CONSTRUCTION` for this synthetic host-only method boundary.

The naive pre-fix rule failed first: it returned `CONFIRMED_OMISSION` for both worlds instead of `UNKNOWN_TELEMETRY`. No ground-truth label was passed to the candidate.

## Limits

No container, live app, physical input/effect, real telemetry-loss rate, task outcome, safety rate, workflow-wide conformance, or product claim follows. The project requires a separate Docker rung and continued full desktop-path integration.
