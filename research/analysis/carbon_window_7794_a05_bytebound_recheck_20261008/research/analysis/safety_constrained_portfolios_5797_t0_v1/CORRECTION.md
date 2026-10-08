# Evidence checksum correction

The original Draft PR #5806 recorded the candidate/auditor stdout hashes from a Windows CRLF working copy. That does not match the UTF-8 LF bytes stored in the GitHub blobs. The result content and decision are unchanged.

For this successor publication, `candidate.raw.json` and `audit.raw.txt` were fetched from the original GitHub branch using the GitHub MCP base64 representation and SHA-256 was computed over the decoded remote blob bytes. The corrected hashes are in `SHA256SUMS`; all entries were then verified against this LF working copy. No candidate, audit, test, threshold, or raw outcome was rerun or altered. This is a provenance repair only, not a new scientific result.
