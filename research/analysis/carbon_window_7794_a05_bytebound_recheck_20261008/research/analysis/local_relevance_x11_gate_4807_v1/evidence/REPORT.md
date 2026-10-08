# Issue #4807 formal result — PASS_LEARNED_X11_GATE_SCOPED

## Decision

The aligned-delta CNN reached the predeclared **0.98 confidence gate without threshold adjustment** on two wholly held-out fresh layout families. It suppressed **16/16** clear irrelevant rows (100%) and forwarded **24/24** relevant-or-critical rows, with zero false suppressions. Critical override forwarded all 8/8 critical rows. The independent raw audit passed every source-hash, exact O3 region, split, decision-rule, and mutation gate. The frozen bounded criteria therefore PASS.

This is a scoped result for newly authored synthetic Tk/X11 fixtures only. It is not evidence for deployment, real-app transfer, task success, runtime safety, or general product relevance.

## Formal source and environment

- Frozen branch `research/local-relevance-x11-gate-4807-20260927`, source commit `f62c6acf70cbce76d456ce54c5e91a725890f054`, based on main `ebc9157e2c3101c073a0405c90432927078c6f15`.
- Source blobs: `README.md` `4f85391ce63f6a3e4942474ed2f5fb47a9b0f37a`; capture `fdaca0a37d374154d1f8cbc8cec2e4f6aaa351c8`; no-write smoke `d1cb7bdd3cdfa9fe8056e3ad3ddaf28b75f17049`; model runner `e024a113c6a966ed958855eaf4897d79a505cf67`; raw auditor `27fe18cbd1da129df6ff298ecbfc5b045a7ff913`.
- Smoke `PASS_X11_API_SMOKE`: Canvas XGetImage 320×240, depth 24, visual 33, 32 bpp, 307,200 bytes; dataset not written, model not called.
- Capture: exact local `codex-x11-preflight:local` image ID `sha256:a27c1782065d2240547482d4e0327d54b1a58cf3e45bf0a0326115822337c48a`, linux/amd64, Xvfb `:173`, Tk Canvas XID 2097162. One capture, 160 pairs/320 raw frames; 120 train pairs from families 0–5 and 40 held-out pairs from families 6–7. Each family: 8 irrelevant, 8 task-relevant, 4 critical. Exact raw format 320×240, depth 24, 32 bpp, byte order 0; 98,304,000 raw frame bytes total.
- Fit: exact local `pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime` ID `sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`; CPU only, CUDA unavailable, one Torch thread. Seed 4807, 174 parameters, Adam 0.01, 120 full-batch steps, cross entropy, fit time `2.6158796149975387` seconds.
- Model SHA-256 `b4af7aee1e941c841d3ca88a7c70f76c2a0feff9e7669cb5db0c788c22b5db21`. Held-out irrelevant `p_irrelevant` min/median/max `0.996282/0.997162/0.998847`; relevant max `0.000880`; threshold remained 0.98.
- Independent audit: `PASS_RAW_AUDIT`, errors `[]`; 160 pairs, all 98,304,000 raw bytes verified, 0 O3 label mismatches, 0 false suppressions, 16/16 irrelevant suppressed, 8/8 critical overrides, 6/6 mutation controls passed (raw integrity, missing, stale, ambiguous, critical, threshold policy).
- Machine-readable capture metadata SHA-256 `911c61fc2f3243826d2f202770f4863d4743a574a5291855b395ca13b1b90f4b`; 160-row per-frame manifest SHA-256 `77e6935bd9622513ebf783bf4a478973f580e0da334c5f62f93c485b3d4040cd`; fit/eval JSON SHA-256 `982ec2f702e63899efeb9240566073707cb8689cb7f04012675f25c44d826132`; audit JSON SHA-256 `83871cb96f5deea3ec9f89a3d773dc1782e233cc70385a6c369f70c088850d03`.
- Lossless capture bundle `capture-bundle.zip`: 1,267,134 bytes; SHA-256 `68bc12177869872acb67a0f6d1c3c825ae6a41741b651fe441c62be1c57382d8`. It contains native per-frame compressed bytes, pair manifest, and capture metadata. The checkpoint and per-row fit/audit outputs are separately retained.

## Lineage and boundaries

The predecessor #4802 HOLD remains unchanged: on its frozen two-channel CNN, 0/16 held-out irrelevant rows reached the 0.98 gate despite zero unsafe suppression. #4807 used a fresh capture with new palettes, layouts, task/critical regions, and completely new held-out families. Its only feature change is a predeclared third spatial `delta ∩ task_ROI` channel; no #4802 held-out data, threshold tuning, alternate seed, retry, GPU, network, package installation, runtime modification, user data, or provider was used.

The model never has authority to act. Critical rows are always fully forwarded; missing/stale/ambiguous provenance yields. The O3 exact-pixel oracle provides the independent comparator. Scope remains eight authored synthetic layouts, one seed, and this one Xvfb format.

