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
- Historical manifest snapshot: [`PRELAUNCH_FREEZE-fe2dbe361940.md`](freeze-manifests/PRELAUNCH_FREEZE-fe2dbe361940.md), copied byte-for-byte from [`PRELAUNCH_FREEZE.md` at commit `fe2dbe3619403b4b356bc0bd365f548a21030812`](https://github.com/Unjuno/agent-interface/blob/fe2dbe3619403b4b356bc0bd365f548a21030812/research/doom/v39_eof_formal_59_f03_20261004_3cbf/PRELAUNCH_FREEZE.md)
- Historical freeze Git blob: `8a8fab7ec3da0c6b9fac17cff87c50b228b93b87`; tree: `868b6ef0d40e73a429e92d5127fbfac05b40c366`; snapshot SHA-256: `bf812996ae896282ba9bc311fa68cb65206d3e5984ff958710fe73b382fb90a1`

The archive was found at the retained host path `/tmp/f03-final-freeze-40b57f74f4.tar`. The archived bytes are copied unchanged here so the independent reviewer can recompute the outer digest and inspect the exact members. `verify_archive.py` validates the manifest snapshot against its historical Git blob identity, then reads the archive digest and member hashes from that snapshot and checks them without extracting files. The commit is retrievable from GitHub's commit and contents APIs even though it is no longer reachable from a current branch ref.

This readback clears only the missing retained-byte/member evidence. It does not clear the immediate prelaunch VM/container/output collision inventory, authorize the formal producer or auditor, or claim that either has run. The frozen protocol still requires a fresh launch-boundary inventory and in-container pre-exec hash checks.
