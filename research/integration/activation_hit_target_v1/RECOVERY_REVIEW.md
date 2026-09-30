# Full-tree recovery review — Issue #4084

This additive `restored/` subtree materializes the exact 280-file patch already
retained on `main` by merged PR #4147. It does not change or overwrite the
capsule, manifest, or reconstruction tooling at this directory's root, and it
does not rerun the consumed GUI/input allocation.

## Integrity and scope

- The 13 committed patch parts reconstructed to 1,315,836 bytes, 12,441 lines,
  SHA-256 `00de864817f10d1b0bc24acbef1fcbdae89adbeafd5414e28a8d8545cb39efd5`,
  matching `PATCH_MANIFEST.json`.
- `git apply --check -p4 --directory=research/integration/activation_hit_target_v1/restored`
  passed; applying it created exactly 280 files under this additive subtree.
- The restored `SHA256SUMS.json` verified all 279 listed files (the manifest is
  self-excluded), with zero length/hash mismatches.
- In a read-only, network-disabled Docker container, the retained raw-only
  `audit.py .` exited 0 and reproduced `AUDIT.json` byte-for-byte; `controls.py`
  rejected 12/12 copied-evidence mutations; `test_policy` passed 7/7 tests.
- This was storage/audit/test replay only. No Xvfb, Tk GUI, XTEST input, or formal
  allocation command was invoked.
- The recovered tree is the original source/evidence delivery identified by
  PR #4147. The prior `research/issue-4084-activation-hit-target-20260922`
  branch is only a superseded, incomplete 14-fragment transport attempt.
- Scientific disposition remains `PASS_ACTIVATION_HIT_TARGET_BOUNDARY_SCOPED`;
  the two `HIT_AND_FOCUS/COVER_AFTER` collateral Button effects remain included.
  No universal click-safety, production, or runtime-adoption claim is made.

The original conversation ZIP hash remains
`a9d6b39b5f7df6ba0952008e7df424c32ff25a4307d3a5df68af94ce262099d4`. This
recovery validates the published patch, not the unavailable conversation ZIP.
