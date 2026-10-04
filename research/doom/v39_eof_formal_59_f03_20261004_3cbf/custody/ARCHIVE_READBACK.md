# F03 exact input archive readbacks

Date: 2026-10-04. This additive custody record preserves two exact source archives named by successive F03 freezes. The first is a predecessor freeze; the second is the current final freeze. These records do not change either freeze, the source tree, or any formal allocation input.

## Current final freeze

- Archive: `f03-formal-freeze-6d8387caa8.tar`
- Size: 1,720,320 bytes
- SHA-256: `786dafda0057e809b5b5f32488899a544e07ad856323d0f635017681704b6344`
- Frozen manifest source: final-freeze commit `43f9a0008bf75da19865cfdea2898d1b896fbbc3`; tree/source commit `6d8387caa8a004ebbdadc377e499b85b3b3a10db`
- Member check: exactly eight regular files; every SHA-256 matches the current freeze manifest; no symlinks or other special entries
- Verifier: `verify_final_archive.py`

The bytes were copied unchanged from `/tmp/f03-formal-freeze-6d8387caa8.tar`; the verifier recomputes the outer digest and all frozen member hashes without extracting files. This current final archive supersedes the predecessor below for any future review, while neither archive by itself authorizes launch.

## Predecessor freeze

- Archive: `f03-final-freeze-40b57f74f4.tar`
- Size: 1,720,320 bytes
- SHA-256: `a70555a7c3c356c3c0175abb9a4a8497df5cfe93bdaf1b71082169cdb6bddcc9`
- Expected digest in the reviewed freeze: the same value
- Frozen manifest source: commit `fe2dbe3619403b4b356bc0bd365f548a21030812`
- Member check: exactly eight regular files; every SHA-256 matches the freeze manifest; no symlinks or other special entries

The archive was found at the retained host path `/tmp/f03-final-freeze-40b57f74f4.tar`. The archived bytes are copied unchanged here so the independent reviewer can recompute the outer digest and inspect the exact members. `verify_archive.py` performs both checks without extracting files.

This readback clears only the missing retained-byte/member evidence. It does not clear the immediate prelaunch VM/container/output collision inventory, authorize the formal producer or auditor, or claim that either has run. The frozen protocol still requires a fresh launch-boundary inventory and in-container pre-exec hash checks.
