# Issue #6155 T0f pre-candidate integrity STOP

**Disposition:** `STOP_PREREG_SOURCE_HASH_MISMATCH`  
**Allocation:** `MULTIFIDELITY-6155-T0F-ANYTIME-CPU-20261003-01`  
**Candidate / auditor / retries:** 0 / 0 / 0  
**Scope:** provenance gate only; no scientific outcome was generated.

## Frozen provenance

- Issue: [#6155](https://github.com/Unjuno/agent-interface/issues/6155)
- Frozen branch: `research/6155-t0f-anytime-validity-20261003`
- Frozen base main: `024ba046557b85d6921f114f65b5d18a79841843`
- Latest launch main checked: `c33380b3b08792a331ee11f7aee05e3d41437e3e`
- Frozen source commit: `7a2e593e8783179580d84654814105e9d35bbfae`
- Freeze-record commit: `46cfbcf9ee99c5394f755b3d45cd1c0e6f876f29`
- Runtime checked: CPython 3.11.9, Windows host CPU.
- The frozen manifest declares the two-commit main advance archive-only and unrelated to the issue, protocol, and source. The same four package blob bytes are present at both frozen commits.

The protocol requires exact source/readback hashes and says to stop if they differ. SHA-256 values below are from the committed Git blob bytes at the frozen commit (independently checked against the checked-out file bytes); the manifest's expected values do not match:

| File | Expected by `FREEZE.json` | SHA-256 of frozen Git blob |
|---|---|---|
| `PROTOCOL.md` | `3c6be0ff6cc69c21a1b61cc3487c0190228c1270842f810c5aecfb994eeadab1` | `7864d888f785921a0c1d40cc3f3ef4881cde592ebcfc32a8d13586dc0f0014c5` |
| `fixture.json` | `f2ffb526d8dedd62af2b85f2e48dfd51bb0f94c56a1f41fa1dbab804b1c7f67e` | `3b70467cadd06606c1e04b5a52fb2b0a4b64f0e85469314b562987848c9dd366` |
| `candidate.py` | `7d49fdfdca263cbaaaa9da4fa78f4ecb8aeaca27485e94f278952187bfc1cf20` | `b804d6d7c38484779bea1a5edc66c9cb235841819d63916b361d41019dedb56b` |
| `audit.py` | `f4cff1851170f9a007993de91b3f697fcba2a65b5554ca6a69acabdccbee7083` | `de5ca0c41f8854ec35291050808799e61f9e748afdd3d18614a914d10220c2fe` |

This is a pre-candidate integrity STOP, not a candidate FAIL or method result. No bytes in the frozen package or its manifest were edited to force a match. The prescribed raw-output directory was absent before the check and remains unpopulated; no candidate or auditor output was created. No GPU, model/provider, GUI, container, WSLc, or task input was used. GitHub network access was used only to retrieve and verify the frozen source and current-main state.

Do not resume or retry this allocation, alter its seed, or substitute outputs. Any future attempt would need a separately reviewed successor with a new freeze and allocation. This record does not resolve whether the mismatch originated in the manifest or source-preparation process.
