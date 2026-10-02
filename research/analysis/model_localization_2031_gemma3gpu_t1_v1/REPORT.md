# Issue #2031 T1 — local multimodal localization result

**Disposition:** `NO_MODEL_UTILITY_DEMONSTRATED_ON_THIS_SYNTHETIC_ALLOCATION`
**Protocol note:** auditor cap exceeded after preserving an initial infrastructure STOP; do not call this a clean protocol PASS.
**Allocation:** `issue2031-gemma3gpu-t1-20261002-01`

**Artifact integrity hold:** the retained `SHA256SUMS` manifest has 113/114 entries matching committed Git-blob bytes. Its `REPORT.md` entry is unresolved: expected `1bbd2132…abd90`, committed bytes hash `2b35b838…05437`. The original contemporaneous report bytes matching the manifest were unavailable in the inspected history. This qualification does not alter candidate outputs, but the report's manifest binding is not verified. Do not treat this package as an all-gates formal PASS or regenerate the historical bytes as if original.

The four-arm comparison ran 32 of 32 fixed cells once using local Gemma 3 4B in a GPU-enabled WSL Podman container. A separate network-disabled auditor eventually reconciled 32 request/response rows. One initial auditor launch failed before analysis because its output destination was read-only; after redirecting output to a writable evidence mount it was invoked a second time. Candidate data were unchanged and not rerun, but the preregistered auditor invocation cap was one. Therefore this is a retained diagnostic audit result with a protocol deviation, not a formal all-gates pass.

| Input arm | Correct | Request bytes | Image bytes | Prompt count | Output count |
|---|---:|---:|---:|---:|---:|
| Full resolution | 1/8 | 294,146 | 216,976 | 3,268 | 168 |
| Overview + candidate crop | 1/8 | 426,355 | 315,626 | 5,713 | 168 |
| Overview only | 1/8 | 283,546 | 209,018 | 3,252 | 167 |
| Candidate crop only | 1/8 | 147,059 | 106,608 | 3,273 | 136 |

Both target-present tasks where the truth-independent crop omitted the target were incorrect in crop-only (2/2). The combined overview-plus-crop input was largest in request bytes, image bytes, and prompt-evaluation count. This tiny synthetic allocation does not demonstrate utility or an attention representation; no runtime promotion is warranted. It does not estimate population error rates.

GPU use was observed during the allocation: Ollama reported Gemma 3 `100% GPU`; `nvidia-smi` reported RTX 3080 Laptop GPU at 42% utilization and 3927 MiB used. The container inference image was pinned and Ollama cloud disabled.

**Interpretation correction:** each arm's 1/8 aggregate is not a proper correctness count. The frozen scorer required `abstain` to be an explicit Boolean, while successful model selections omitted that field; these structurally incomplete selections were all scored false (`invalid_abstention_type`). Thus the observed numeric summary reflects a response-schema/scorer incompatibility as well as localization, and cannot establish that all arms truly localize at 1/8. Preserve that mismatch; do not relabel or patch the original audit. The direct raw outputs show model-provided coordinates and labels, but target-coordinate correctness must be reconsidered by a separately preregistered successor with an unambiguous schema rule. Existing result remains no demonstrated utility and no promotion.

See [FREEZE.md](FREEZE.md), complete byte-exact candidate/audit bundle in `research/analysis/model_localization_2031_gemma3gpu_t1_v1/formal/`, and the preregistration/deviation notes on [Issue #2031](https://github.com/Unjuno/agent-interface/issues/2031). Prior #1968/#2173 evidence is unmodified.
