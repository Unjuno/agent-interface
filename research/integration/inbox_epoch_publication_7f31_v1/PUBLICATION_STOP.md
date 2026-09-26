# HOLD_RAW_PUBLICATION_INCOMPLETE

The assistant-mediated text transcription of compressed evidence introduced
changed/truncated bytes. This is not evidence that GitHub altered an accurate
request, and not a failure of the formal experiment. The API stored the
submitted text; the assistant's publication copies did not match the local
original. No scientific rerun or relabeling was performed.

The incorrect copies are quarantined under TRANSPORT_FAILURES and remain
reachable in their original commits. They are not admissible raw evidence.
No incorrect file remains at the authoritative RAW.json.gz.b64 path in the
PR head. GitHub-only reconstruction is still incomplete, so the PR is Draft
and must not be merged as a completed evidence delivery.

| Copy | Actual Git blob | Expected Git blob |
|---|---|---|
| First full raw, commit fca42b100c5ba1ecf93ef35620d93edd69eff2cb | 72db86d6dc9f74f7d0fafeff405c51ca19aae064 | 0a9947f3faf3979cf7bb13731da1b874cf88b2b1 |
| Second full raw, commit 7f2db9fdadeb1b881be5ffbb81a1f5de4ce07daa | befa8046f27bc1ea98cc81916c1c2bf61fc5f382 | 0a9947f3faf3979cf7bb13731da1b874cf88b2b1 |
| Raw part 00, commit 15aa872d3adf1ac74653b7f930819629b27b1af4 | daacab4bd673092a0450b44ea0fe75f3585b0f57 | c76cdcc2e9e06f2a90b1ce1bb0e23c9dd19bb9bf |
| Unreferenced raw part 01 upload, quarantined here | 05c6b884ba1fddd2d51aa2c1a8bbb3501b95b207 | cd66ceaf89b04ac5fa4ce2c07241edd8d0d17747 |

The local raw original remains 288,509 bytes with SHA-256
`eef12b6de49f12f34cc86dca0dcea0d66986ed739d9cfc3adf640c966b6a403a`.
The exact compressed base64 original remains 12,438 bytes, SHA-256
`79ca5b7d80db5b5b854e5887f98b274cd605ca2ee97e8fc912f48b849bae9773`.
Both are included in the conversation evidence archive. The full construction
archive, all case-level files, frozen source and exact audit outputs are
retained there as well. The archive is not assumed available to GitHub-only
workers.

Verified local/published frozen Git blobs:
- run.py: `8886f8aba9be2bfd26789f47ad20b7bfd95366fa`
- audit.py: `2a77cd9f3988ab8d756b6116a7daed4c7f0af66a`
- PLAN.md: `672b2cbcc1bcf1367dce3c271d3589f8e48a2964`
- FREEZE.json: `b7f88e74dc7b9cacbed5e396a1f4947bc2109367`

Resume criterion: publish the unchanged original bytes, verify their complete
Git blob/SHA-256 identities after read-back, run the frozen auditor read-only
on those recovered bytes, and complete ordinary PR review. Do not consume a
new formal allocation merely to repair publication.
