# Exact provenance for the PR #7414 rescued outcomes

The original branch is `fix/59-v39-candidate-network-receipt-20261004`.
PR #7414 (`https://github.com/Unjuno/agent-interface/pull/7414`) is based on
Draft PR #7386, which is based on Draft PR #7355. This package does not merge
that stacked source tree into current main.

## Recorder-boundary probe

- Final source commit: `7d88e2a0ed2fae881c79e205564e67326802c5be`.
- `research/doom/map01-v39-per-key-release-live-t0-20261004/candidate.py`:
  Git blob `a3e81226556461cc6da4184576c9841468c516f4`, SHA-256
  `663f5205d4118ee404d12e0cca078ab16d0a93f94045447c52cfb02c642a23f1`.
- `.../test_candidate.py`: Git blob
  `6e17c62ce1cc80884b2339c2e6232bc8f861d1c6`, SHA-256
  `86b13e0ed5640d1b5900aabb44851f5f7a1a3b5c56dfcf57ec211ff0d25e933c`.
- Original result files and hashes from that commit:
  - `results/recorder-boundary-probe-20261004/BASELINE_RED.json` —
    `32b47ed7f1c1c1829d8541847195d22a247d244b898ab94fb02ae77dddef1449`
  - `.../CONSTRUCTION.txt` —
    `3db5d0e9d74df9fe4cc809d7068d011a18145af56c48516c42eadd94d7069ab4`
  - `.../RESULT.md` —
    `b6ff7868ffa0daf4805bb406fa31a63547395612a457a15c4e2a00af207819d1`
  - `.../RESULT.json` —
    `92cd5db3a4d4e216022889b2a65ed3f828072a525e652764db0071b1cd4714dd`

## Malformed-auditor-input probe

- Pre-fix auditor: commit
  `eb11a9d05e05e0c078ab5ac151d47cc6f47644ba`.
- Corrected test/auditor lineage: commit
  `79d96a5becc47131708211be24d52a4c5714ae56`.
- At the corrected commit, `audit.py` Git blob
  `8c8a4eb4998e2cbc3e3302eac6e29d33e390e156`, SHA-256
  `8ac20e5a1e546706e6bf6b6d45606dfc4b431c6d474e8d463333b83b103c3f10`;
  `test_audit.py` Git blob `b7e0ededfeebdfbbf4f50820aa280b1e31e2f5c9`,
  SHA-256 `e27f1e8789c72cbc0d61e41457413d19d31239b89f273be36a1eb2c1c73c5565`.

The original `SHA256SUMS.txt`, full baseline/candidate test outputs, probe
report, source, and tests are retrievable with `git show` from the exact PR
commits above. Their hashes are transcribed from the original manifest; this
package does not claim that those remote source files were copied byte for
byte here.
