# Astra HUD sampling alias A03

## H/T/D/C/U

- **H:** Periodic observation intervals of 0.4 s or 0.8 s may retain most of the A01 high-change samples regardless of phase.
- **T:** Enumerate every phase of stride-2 and stride-4 periodic downsampling over the immutable 5 Hz A01 ROI sequence.
- **D:** One deterministic phase sweep over 780 contiguous frames. Raw source commit `5e5fa2e697109dc68a605bbfcb04e523e3103698`; raw CSV SHA-256 `0b585a3671a10ba2a3e4f634b32cddc7f3fb83aa85013eb75faff8a128cd7e97`.
- **C:** Event = frame after source time 31 s with red-mask XOR >60; stride2=0.4 s, stride4=0.8 s; event observed iff its frame index matches the sampled phase.
- **U:** Retrospective sampling-resolution analysis only. No labels for threat, damage, useful feedback, safe response, or task effect.

## Result

The hypothesis is falsified on this trace. Of 30 defined excursions:

- At 2.5 Hz (stride 2), phase 0 observed 14/30 and phase 1 observed 16/30.
- At 1.25 Hz (stride 4), phases observed 3/30, 8/30, 11/30, and 8/30.

Thus the observed count depends materially on sampling phase and cadence. Even the best 1.25 Hz phase found 19/30 excursions absent. These are mask-transition samples, not semantically validated events.

The A02 neighbor-persistence result showed zero adjacent >60 samples at 5 Hz. Together, A02/A03 warn that a generic persistence gate or coarse periodic sampling can erase brief visual changes; they do not justify acting on raw pixel changes. A live semantic-observation/reaction test still requires its own authorization and independent task-effect scoring.

## Reproduction

Run `node analyze.mjs` with Node.js 18+ and network access. The script fetches the CSV by immutable commit SHA, verifies 780 contiguous frames and exact 0.2 s cadence, then enumerates every phase. Local Node.js 24.6.0 reproduction returned counts `[14,16]` and `[3,8,11,8]`.
