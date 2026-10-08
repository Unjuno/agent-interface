# Attempt log — Issue #5800 T0

1. Frozen candidate execution: completed once with Python 3.12.10; emitted 512 profiles and the five declared controls. Candidate was not rerun.
2. Initial auditor invocation from the repository root: failed before reading output because its input path is relative to the experiment directory. No candidate rerun followed.
3. Auditor run from its expected working directory: `FAIL_AUDIT`; 511 `mutation_identity` errors. Root cause: candidate mask bit 1 denotes an injected false dimension, while auditor reconstruction interpreted bit 0 as false. Raw candidate and failed audit are retained unchanged.
4. Corrected only the independent auditor's mask reconstruction, preserving the candidate and candidate raw. The separate `audit.corrected.raw.txt` reports `METHOD_PASS_SCOPED`, zero errors, 512 profiles, 511/511 injected faults detected, intrusive negative control failed, unavailable AT oracle held.
5. `pytest -q test_candidate.py`: 4 passed. Docker Desktop daemon/WSL backend did not answer `docker --context desktop-linux info`; no container or image was used.

The corrected audit is a transparent repair after a failed audit, not an independent fresh allocation and not evidence of UI, assistive-technology, participant, or product behavior.
