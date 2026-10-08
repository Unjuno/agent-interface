# T0f provenance STOP — local exploratory output is not formal evidence

**Disposition: `STOP_PREREG_SOURCE_HASH_MISMATCH`.** The allocation's committed GitHub source bytes do not match the SHA-256 digests recorded in `FREEZE.json`. The candidate and auditor were mistakenly run once each against the local files whose digests matched the manifest, before the committed Git blob bytes were independently compared. The results in `REPORT.md`, `RUN_RECORD.json`, and `raw/` are retained as forensic exploratory output only; they are not a valid formal result and must not be promoted or merged as scientific evidence.

At frozen source commit `7a2e593e8783179580d84654814105e9d35bbfae`, direct GitHub base64 retrieval and byte decoding confirmed these SHA-256 pairs (manifest expected / actual committed blob):

| File | Manifest expected | Committed blob |
|---|---|---|
| `PROTOCOL.md` | `3c6be0ff6cc69c21a1b61cc3487c0190228c1270842f810c5aecfb994eeadab1` | `7864d888f785921a0c1d40cc3f3ef4881cde592ebcfc32a8d13586dc0f0014c5` |
| `fixture.json` | `f2ffb526d8dedd62af2b85f2e48dfd51bb0f94c56a1f41fa1dbab804b1c7f67e` | `3b70467cadd06606c1e04b5a52fb2b0a4b64f0e85469314b562987848c9dd366` |
| `candidate.py` | `7d49fdfdca263cbaaaa9da4fa78f4ecb8aeaca27485e94f278952187bfc1cf20` | `b804d6d7c38484779bea1a5edc66c9cb235841819d63916b361d41019dedb56b` |
| `audit.py` | `f4cff1851170f9a007993de91b3f697fcba2a65b5554ca6a69acabdccbee7083` | `de5ca0c41f8854ec35291050808799e61f9e748afdd3d18614a914d10220c2fe` |

The downloaded committed files were 2 bytes longer than the local run inputs in each case. The discrepancy is consistent with a line-ending difference, but its origin is unresolved. The STOP's raw-byte hashes were independently reproduced by decoding GitHub's base64 file response and hashing the resulting bytes locally.

Candidate and auditor each ran once (20,000 candidate rows; independent replay reported 0 row mismatches and rejected 4/4 corruption controls). Those observations describe the local manifest-matching files only. They do not repair the source-integrity gate. No retry, substitution, or rerun is authorized under this allocation. Preserve the original STOP PR #6792 and this forensic package; any future test requires a separately reviewed successor allocation with bytes frozen and verified from GitHub before execution.

