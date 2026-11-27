# Evidence transfer integrity note (2026-10-22)

This packet was transferred from PR #9315 head `76626da8b03df25024d12efb5f1dde2f12c53ed2` after PR #9320 merged the focused runtime slice. The source inventory contains 183 distinct paths named by 20 SHA256SUMS files. 182 paths were restored byte-for-byte from the retained local packet and each matched its frozen digest. Forty-eight manifest-referenced files were absent from the PR Git tree but were present in the retained local packet with matching hashes.

The PR's root checksum file listed `README.md` as `dccbaee929630b39d44e3bce51b037bd48fbd60b9e737985c7508617e3f37daf`, which did not match the README bytes in the published PR. The README itself is retained unchanged at SHA-256 `8d34b2b4d2aeae8a0dfa012e4720d93df0d3cb1d1d0b3f10f546c076884728f6`; only that stale index digest was corrected. The original digest and mismatch remain visible in PR #9315 history. Run conditions, raw results, failure outcomes, source snapshots, and per-run manifests were not edited.

The packet now has a path-specific `-text` attribute so Git does not normalize the captured bytes on Windows. Credential-pattern scan returned no matches. The separate archived design proposal was not copied here because its release-boundary recommendation conflicts with the later corrected-source evidence; it remains pending explicit historical disposition.
