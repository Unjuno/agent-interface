# F03 exact input archive readback

Date: 2026-10-04. This additive custody record preserves the exact source archive named by the F03 freeze. It does not change the freeze, the source tree, or any formal allocation input.

- Archive: `f03-final-freeze-40b57f74f4.tar`
- Size: 1,720,320 bytes
- SHA-256: `a70555a7c3c356c3c0175abb9a4a8497df5cfe93bdaf1b71082169cdb6bddcc9`
- Expected digest in the reviewed freeze: the same value
- Frozen manifest source: commit `fe2dbe3619403b4b356bc0bd365f548a21030812`
- Member check: exactly eight regular files; every SHA-256 matches the freeze manifest; no symlinks or other special entries

The archive was found at the retained host path `/tmp/f03-final-freeze-40b57f74f4.tar`. The archived bytes are copied unchanged here so the independent reviewer can recompute the outer digest and inspect the exact members. `verify_archive.py` performs both checks without extracting files.

This readback clears only the missing retained-byte/member evidence. It does not clear the immediate prelaunch VM/container/output collision inventory, authorize the formal producer or auditor, or claim that either has run. The frozen protocol still requires a fresh launch-boundary inventory and in-container pre-exec hash checks.
