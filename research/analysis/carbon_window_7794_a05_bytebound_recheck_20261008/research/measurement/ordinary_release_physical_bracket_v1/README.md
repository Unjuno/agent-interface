# Ordinary release physical bracket contract v1

Issue: #992  
Task: `ORDINARY-RELEASE-PHYSICAL-BRACKET-CONTRACT-20260917-001`  
BASE: `e23de8af15d3658e18e6a54f69fba966e5c3e4f3`

Decision: **PASS_PHYSICAL_RELEASE_BRACKET_CONTRACT_SCOPED**

## H

A release receipt may expose a physical key-up interval only when one serialized owner operation retains: owner ownership; physical DOWN sampled immediately before release; release attempted; sync succeeded; physical UP sampled after sync; and ordered same-clock timestamps.

The conservative physical interval is `[pre_sample_end, post_sample_end]`. Other valid states produce typed no-interval outcomes; malformed/inconsistent evidence fails closed. The receipt grants no authority and does not claim application consumption.

## T

Pure standard-library contract plus an independently implemented truth-table/oracle. Exhaust every relevant boolean combination over four timestamp spacings, then run 200,000 seeded randomized timing/state cases. Parent controls include a #990-style already-UP no-op, a fully bracketed release, removal of post-UP confirmation, one-at-a-time required-witness ablations, malformed lineage/type, and invalid timestamp ordering.

## D / result

- exhaustive cases128; candidate/oracle mismatches0;
- contradictory exhaustive cases rejected64;
- exhaustive confirmed physical intervals4;
- fixed parent/ablation/malformed controls15/15;
- random cases200,000; candidate/oracle mismatches0;
- random confirmed physical intervals6,126;
- false physical intervals0;
- every emitted interval exactly `[pre_sample_end,post_sample_end]`;
- digest `e4f50be0628a895c9e4ca804e1a81f66fbe1121bc11e6fd0c74d5a3b8ea8c023`.

Container diagnostics: wall6.59s, max RSS93,104KB. No performance claim.

SHA-256 of construction source/result before publication:
- contract `fc3a74cf288ea0ec41002686fe1ca74e4ff0d1f13e891c866910c56ab9e0f6d8`;
- test/oracle `91c0dd4b0db686123f7843fb183d6f14b35ae61de9de5cac65f17dfd1f625aca`;
- result `db8627f051b52b28ab9c452acc764940999ea80aba9812941bf9ba23fd937518`.

## Interpretation

#990 showed that a release-RPC envelope cannot distinguish a transition from a no-op. This result defines the stronger evidence needed before #981/#988 may consume an ordinary up as a physical edge: last confirmed physical DOWN before release and confirmed physical UP after sync, inside the same serialized owner operation.

This is a temporal bracket, not causal proof. Another actor could alter the physical state between samples; application consumption is separate.
