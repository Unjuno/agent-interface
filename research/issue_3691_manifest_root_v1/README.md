# Issue #3691 manifest trust-root reproduction

## H/T/D/C/U

- **H:** The open Issue #3691 auditor authenticates raw and predecessor-freeze bytes using digests loaded from a caller-controlled study manifest. If that manifest is replaceable, coordinated replacement of raw + predecessor freeze + study manifest can recover PASS despite all internal checks.
- **T:** Reproduce the exact PR #3697 reported exploit and current Issue #3691 branch source without modifying either branch. Use exact source and evidence from GitHub blobs, verify source SHA-256 and canonical evidence digests, then construct replacement raw/freeze/manifest in a temporary directory. Compare canonical invocation to coordinated replacement invocation and preserve original evidence byte-for-byte.
- **D:** PASS_REPRODUCTION if exact current source returns PASS for canonical artifacts and for a self-consistent coordinated replacement; FAIL if replacement is rejected; STOP if inputs cannot be reconstructed. Tests the trust-root boundary only, not Docker validation or XRes.
- **C:** No repository checkout mutation, no Docker/container invocation, no network in the local harness, no X11/GUI/input/model execution, no formal allocation rerun, no modification of predecessor evidence or PR #3697 branch.
- **U:** Demonstrates this specific artifact-authentication gap only; not arbitrary auditor unsoundness or runtime/security claims.

## Exact inputs and reproduction

Tested current branch `research/issue-3691-audit-integrity-v1` at HEAD `71ab9b6a0149695184282bc200cc544290fa42bb`.

- Auditor Git blob `67fdda7cdd141803351ff98825b68c08728413e7`; SHA-256 `0956b13a9e98c504c870096507b9428acae0510a27903d0eccb0f730af35c579`.
- Raw Git blob `5bea90956ecf5cf0ec130f72b18769bebb01f9b0`; canonical SHA-256 `ccb9a75eefb7df73cb13dbc9191d33334fb672c2fd58fcc5fa32be998e182807`.
- Predecessor FREEZE Git blob `4831ebb5657789fd12e694d366844d1a2432ba36`; canonical SHA-256 `f40494b1be99fb1e68d7b09c498297df35a72c043740b5f09d3faec7e059acfe`.

Python 3.12 temporary-directory harness. Canonical invocation: exit 0, `PASS_OFFLINE_STRUCTURAL_AUDIT`, `errors=[]`; all 11 internal corruption controls true. Challenge changed both pixel digests to 64 `1` characters, appended one space to predecessor FREEZE, updated raw.freeze_sha256, and replaced study manifest hashes while retaining the exact auditor/test source hashes.

Coordinated replacement invocation also exited 0 with `PASS_OFFLINE_STRUCTURAL_AUDIT`, `errors=[]`, and all 11 internal controls true. Replacement raw SHA-256 `32eea2e057b34ee0df624dbf5a07e76f3f57807ed55f0d957766a67693dc1377`; replacement freeze SHA-256 `529dbd8f6fbf1181606bb0eed7e1da3dcfe4267dcc8afb6eb023ec593fd9d640`; replacement study-manifest SHA-256 `d658774e7f72e281f144f65b54e010f70e16ec2dbbc62401d2e9f24d4009a4e4`.

## Decision and limits

**PASS_REPRODUCTION_MANIFEST_TRUST_ROOT_GAP.** The study manifest is an untrusted authority: artifact digests are compared only to values supplied in that same replaceable manifest. The current CLI has no independently pinned digest for the study manifest. A fixed external expected digest or immutable manifest identity is required to close this path, together with a three-artifact substitution regression.

This is native static audit reproduction only. It does not clear Issue #3691's required local Docker gate. Docker Desktop on this PC remains unavailable; no Actions substitute, image pull, storage repair, GUI/input execution, or formal XRes allocation was performed.