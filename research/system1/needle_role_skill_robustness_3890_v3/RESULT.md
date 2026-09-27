# Formal result — Issue #4619

Decision: **FAIL_ROLE_SKILL_ROBUSTNESS**  
Audit: **PASS_AUDIT** (0 integrity/provenance errors)  
Allocation: `needle-role-skill-robustness-3890-v3-freshblock`  
Seeds: 913000–913900 (10 fixed seeds; 30/30 Docker invocations; zero retries)  
Frozen source: `FREEZE.json`; sidecar SHA-256 `ca72b9cc1a74e5a7c8ca47dbdfc4b6cf72b8d4276e55330e53f11c1d061f99d4`.  
Image: `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, CPU-only, network-none.

| Role | Mean accuracy | Minimum | Maximum | Seeds below 0.90 |
|---|---:|---:|---:|---:|
| A | 0.96594 | 0.95508 | 0.97046 | 0/10 |
| B | 0.94265 | 0.92627 | 0.96851 | 0/10 |
| C | 0.92402 | **0.80737** | 0.96021 | **1/10** |

The single gate miss is seed **913400 / role C**, 3307/4096 correct (0.807373); the frozen floor requires at least 3687/4096. All other 29 role-seed cells are >=0.90. The 20 isolated loader runs exactly matched independently reconstructed predictions and package hashes; all 20 one-byte corruption controls recorded one changed byte and rejection. The independent audit recomputed all labels/predictions and returned zero errors. Package immutability and graph lifecycle controls passed.

The result is a scoped negative robustness finding: the three-seed #3890 result did not meet its pre-registered ten-seed generalization gate. No seed was excluded or retrained, no threshold or model was changed, and there is no runtime/model promotion. This synthetic task does not establish real-world skill transfer.

Full invocation receipts and independent audit are stored beside this report. Per-seed raw package, expected inputs/labels/predictions, both loader outputs, corruption controls and stdout/stderr are preserved in the archives indexed by `EVIDENCE_INDEX.md`.
