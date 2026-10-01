# Evidence packaging recovery

The source PR head `01043ea3665cb85e1490a9d13306cfa9e8a28780` included four
attempt manifests that each declared `fixture.log` as 0 bytes with SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, but the
four paths were absent from the Git tree. The declared bytes are uniquely the
empty byte string, so this successor adds zero-byte files at those exact paths
without changing the original manifests or any other evidence.

This reconstructs the manifest's declared package contents; it cannot prove
that the original fixture process created those empty log files. No log text or
other runtime output was synthesized. `test_evidence_manifest.py` checks exact
file-set equality, byte lengths, and SHA-256 for all four retained attempts.

The formal three-allocation result remains separately recorded in merged PR
#3636. This construction package makes no new formal or public-MCP claim.
