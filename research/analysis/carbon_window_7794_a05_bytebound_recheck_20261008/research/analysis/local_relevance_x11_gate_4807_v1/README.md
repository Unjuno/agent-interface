# Issue #4807 — fresh-family aligned-delta relevance gate

Successor to #4802 `HOLD_MODEL_NO_SAFE_UTILITY`, itself following the preserved #4799 STOP and original #2188 hypothesis. No prior outcomes are rewritten. The #4802 held-out families are excluded from all #4807 training, selection, threshold calibration, and evaluation.

## Frozen H/T/D/C/U

- **H:** A tiny learned gate with an explicit aligned `pixel_delta ∩ task_ROI` feature can reach confident irrelevant decisions on two entirely held-out X11 layout families at the unchanged 0.98 threshold, suppress >=8/16 clear irrelevant changes, and suppress no relevant or critical change.
- **T:** Eight newly authored 320×240 Tk Canvas/X11 layouts, all with new palette, geometry, and task/critical regions. Capture 160 ordered pairs (8 irrelevant, 8 task-relevant, 4 critical per family); families 0–5 train (120), 6–7 remain held out (40). Freeze exact native XGetImage bytes, raw SHA-256, XID, geometry/pixel format, sequence, masks, source and images before the single formal capture. One CPU fit/eval, then one separate stdlib raw audit.
- **D:** `PASS_LEARNED_X11_GATE_SCOPED` iff zero held-out relevant/critical false suppressions, >=8/16 irrelevant suppressions, all 8 critical cases forward, missing/stale/ambiguous controls yield, and the hash/O3/mutation audit passes. Any unsafe suppression is FAIL. Safe but low utility or audit failure is HOLD. X11 smoke or formal capture failure is STOP, with no training after capture failure and no same-issue retry.
- **C:** Capture `codex-x11-preflight:local` ID `sha256:a27c1782065d2240547482d4e0327d54b1a58cf3e45bf0a0326115822337c48a`; fit `pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime` ID `sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`. Both cached linux/amd64. Docker network none, read-only root/source/data, one CPU, bounded memory, no GPU passthrough, `CUDA_VISIBLE_DEVICES=''`, no package install or external calls. Capture, fit, and audit are separate invocations with distinct empty output subdirectories.
- **U:** One seed, eight authored synthetic layouts, 160 pairs. No real-app transfer, arbitrary semantics, user data, runtime authority, task success, performance, production, or deployment claim.

## Model and guard

The 174-parameter CNN receives max-pooled 32×32 channels for exact raw-pixel delta, task ROI, and their pixelwise intersection (intersection is computed before pooling). It uses Conv(3→4, 1×1), ReLU, Conv(4→4, 3×3), ReLU, adaptive max pool, Linear(4→2). Seed 4807, Adam(lr=0.01), 120 full-batch cross-entropy steps; no post-fit calibration. Suppress only at `p_irrelevant >= 0.98`; a critical ROI always FULL_FORWARD. Missing/stale/unsupported pixel provenance yields before inference. The model is offline and has no runtime authority.

## Freeze and invocation

Run `smoke_x11.py` in the exact capture image with network disabled before freezing; it must validate the Canvas XGetImage geometry/pixel format in memory and write no dataset. Freeze these source files on the isolated GitHub branch, read them back and verify blob identity, then run once each: (1) fresh Xvfb capture into a new child directory of the output mount, (2) CPU fit/eval with data read-only, (3) separate raw-only audit with capture and fit read-only. Never point `OUT_DIR` at the existing bind-mount root. No retries, threshold changes, alternate seed, or holdout reuse after the formal capture begins.

