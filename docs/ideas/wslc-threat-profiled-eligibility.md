# Threat-profiled runtime eligibility for Dockerless WSLc

- **Status:** Blind review ended in disagreement; no runtime was certified as a sandbox.
- **Source:** Issue [#8150](https://github.com/Unjuno/agent-interface/issues/8150).
- **Idea:** Evaluate whether a runtime's effective controls match the threats and protected assets of a specific experiment before using it for untrusted code.
- **Outcome:** Merged [PR #8167](https://github.com/Unjuno/agent-interface/pull/8167) preserves the frozen protocol, cases, two blind reviews, and `HOLD_REVIEW_DISAGREEMENT`. The result does not show that WSLc is insecure, Docker is categorically safer, or any configuration meets a threat model. It authorizes no untrusted-code probe and makes no general resource-isolation, OOM, or parity claim.
