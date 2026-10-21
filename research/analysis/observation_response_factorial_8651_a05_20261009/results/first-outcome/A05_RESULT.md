# A05 corrected raw-only result

- Allocation: `8651-A05-20261009`; workflow run [37805764321](https://github.com/Unjuno/agent-interface/actions/runs/37805764321).
- Upstream candidate: A04, one invocation; A05 candidate invocations: zero. A05 corrected auditor: one invocation, exit 0.
- Immutable input: A04 source-result commit `5351d81439e0f8252d458b804c688b92a03b14ab`; 96-row `RAW.jsonl`; SHA-256 `7c9ef1852727b1906681e6b8d1d36d2592c55c100589551710dcd381beaf600e`.
- A04's original audit is retained unchanged. Its primary interaction value `-0.875` was overwritten by the last forged-effect mutation test because that test mutated shared protocol contrast state.
- A05 reports **PASS_METHOD_SCOPED** and **INTERACTION_SUPPORTED_SCOPED**, with no audit errors; all four mutations rejected.
- Deadline/transient-cue: fixed active-minus-sham `0.0`; reactive active-minus-sham `-1.0`; difference-in-differences `-1.0`.
- Stable and no-decision-information controls: difference-in-differences `0.0` each.
- Container inspection: `network=none`, read-only root filesystem, memory `134217728` bytes, `NanoCpus=1000000000`, `PidsLimit=32`, process exit `0`.
- Claim limit: synthetic deterministic timing/evidence only. It does not establish live GUI/OS, model, safety, mediation, or user-tempo effects; Issue #59 remains open and unaffected.

This is the corrected result summary for the raw-only successor audit. It does not replace the A04 raw file or original audit record.
