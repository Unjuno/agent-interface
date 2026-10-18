# Byte-bound replay of the carbon-window comparator

- **Status:** A05 byte-bound replay passed; the prior A04 metadata integrity HOLD remains.
- **Source:** Issue [#8386](https://github.com/Unjuno/agent-interface/issues/8386), successor to [#7794](https://github.com/Unjuno/agent-interface/issues/7794).
- **Idea:** Reconstruct the exact execution bytes behind a saved comparator run and replay them under a new freeze, separating trailing-newline serialization differences from semantic changes.
- **Outcome:** A05 used the checked-in Git blobs plus one LF byte for four execution files, froze their actual digests, and ran candidate and auditor once each. The auditor reconstructed 10/10 cases with zero differences and reproduced the declared discriminator. The unresolved A04 `FREEZE.json` and preregistration digests remain mismatched; A04 is unchanged. Native Windows 11 CPU-only evidence is not container or WSLc migration evidence and makes no energy/emissions claim. See merged [PR #8393](https://github.com/Unjuno/agent-interface/pull/8393) and [PR #8395](https://github.com/Unjuno/agent-interface/pull/8395).
