# Recovery provenance for the retained XDamage v3 HOLD

On 2026-09-30, [PR #4905](https://github.com/Unjuno/agent-interface/pull/4905) was reviewed for evidence retention from exact head `463ab1f6ac65d26826739bb3e46a2185551371d3`, branch `research/xdamage-temporal-boundary-3935-v3-20260927`. Its twelve original files remain byte-for-byte unchanged. All twelve paths were absent from recovery intake main `4439161abd6f8ccf276babc1c39c43428394e773`.

## Static publication checks

All twelve source Git blob identities matched readback. All seven source-file SHA-256 values in `FREEZE.json` match the published bytes; `exact_gate.py` retains blob `d2629bc94d40cc0a8e1bf9e053585549218629ed`.

- `results/CONSTRUCTION_EVIDENCE.zip`: Git blob `fbde8137d5de606c2c7a6dab1c1c66ec50a177aa`; SHA-256 `ea89636ba125bc4324770c676accf0b4e8a25c40a8dac9a391f7b1a7fc2ce44f`; 12,668 bytes, 32 members, 250,003 uncompressed bytes
- `results/FORMAL_EVIDENCE.zip`: Git blob `f3243509353608071b715cb616590a9fd5fbb2aa`; SHA-256 `b220d1c470d3882d0b8f55558abe6fb066e1c9b23cfd0a524f79802d04b9c824`; 39,563 bytes, 207 members, 1,848,622 uncompressed bytes

Both archive hashes match `results/RESULTS.md`. ZIP CRC checks pass; member names are unique, relative, non-traversing, and not symlinks. In-memory parsing finds six construction rows (one per case) and 48 formal rows (eight per case). All 18 construction and 144 formal baseline/middle/endpoint frame references resolve to archived members with matching SHA-256 values. These are static byte/structure checks, not execution of the retained experiment or auditor.

## Scientific disposition remains HOLD

The allocation remains **`HOLD_PREREGISTRATION_PATH_IDENTITY`**. Exact output-path identities were not publicly frozen/read back before execution; posthoc publication cannot repair that chronology. The original corrected `results/RESULTS.md` and raw archives are preserved without relabeling.

The archived auditor reports 48/48 formal rows, zero audit errors, and nine rejected corruption controls. Those are historical technical audit receipts, not a newly reproduced audit or scientific PASS. This recovery did not run the original runner, auditor, protocol tests, native observer, X server, UI, Docker, GPU, or model. It does not independently attest historical host/image/process execution or rerun corruption controls.

The single formal invocation remains consumed; no retry, replacement, new allocation, runtime adoption, action authority, broad GUI correctness, or Issue #4900 completion is authorized or claimed by this retention. Any later research must preserve this HOLD and establish its own prospective scope and gates.

