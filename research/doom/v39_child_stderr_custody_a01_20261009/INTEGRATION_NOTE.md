# Integration note (2026-10-27)

The original construction records in this directory are preserved unchanged from PR #8730, head `5fd0fc6db1c62c4acd3ba934f632f930d017d472`. Its `FREEZE.json` source hashes bind the files at that PR head, not its stated base/experiment-tree commit. The two hashes were verified against the original PR head. The retained test logs and PASS_CONSTRUCTION refer to that original construction; they are not a test of the current integrated sources.

Current main has subsequently changed both source files. This integration merges the original change into the later versions, and changes the added test child to write bytes, avoiding Windows newline conversion. Therefore the historical `audit.py` checks of current root source files will not match the original frozen hashes. The original auditor and original results have not been rewritten or rerun. See the original PR head for the exact historical source bytes.
