# Issue #4802 — corrected source-bound X11 gate successor

This is an additive successor to #4799 STOP. Preserve #4799 and its pre-capture startup/Xlib failures unchanged. The unchanged local-only learner and raw auditor are reused by exact source Git blob identity: `train_eval.py` blob `9deb0325b54b2818e8463722078ab547b132ed52`; `audit.py` blob `3f0f572c8bffa8f5f6415431f2a2ed18435a5c45`.

## H/T/D/C/U

- **H:** The 234-parameter CPU CNN trained on source-bound X11 pixel deltas from four authored layout families can suppress >=8/16 clear irrelevant changes in two wholly held-out shifted families, with zero relevant/critical false suppressions.
- **T:** A Docker smoke validates Xvfb/Tk/Python-Xlib metadata and one in-memory 320×240 Canvas XGetImage (no saved data, no model). Then one fresh formal Xvfb capture creates 120 ordered pairs from six families (8 irrelevant, 8 task-relevant, 4 critical each), families 0–3 train and 4–5 held out. One frozen CPU fit/eval and one separate offline raw-only audit.
- **D:** PASS_LEARNED_X11_GATE_SCOPED iff zero unsafe suppression, >=8/16 irrelevant suppression, all 8 critical forward, provenance controls yield, and raw/O3/hash/mutation gates pass. FAIL on any relevant/critical suppression. HOLD if safe but utility/audit gate missed. STOP_X11_CAPTURE_PREREQUISITE if smoke or formal capture fails; no fit after capture failure and no same-issue retry.
- **C:** Capture image `codex-x11-preflight:local`, ID `sha256:a27c1782065d2240547482d4e0327d54b1a58cf3e45bf0a0326115822337c48a`; PyTorch image `pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime`, ID `sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`. Local cached linux/amd64, network none, read-only root, one CPU, bounded memory, no GPU passthrough, `CUDA_VISIBLE_DEVICES=''`, source/data read-only, dedicated output only.
- **U:** Synthetic Tk/X11 only, six layouts, one seed. No real-app transfer, user data, runtime authority, task success, deployment, or generalization claim.

## Source/API check

`smoke_x11.py` ran in the pinned capture image with `--network none`, read-only root, 512 MB, one CPU. Result: PASS_X11_API_SMOKE, XID 2097161, 320×240, depth 24, visual 33, 32 bpp, scanline pad 32, image byte order 0, exact 307200-byte XGetImage. It wrote no dataset and called no model. The correction in `capture_x11.py` uses `Display.screen().allowed_depths`; the previous #4799 source remains immutable.

Formal capture output must use a new subdirectory under the bind-mounted host output root (`OUT_DIR=/out/capture`), not `/out` itself. Each formal phase gets its own new subdirectory. Capture/eval/audit source, inputs, decisions, hashes and outcome are retained. No tuning, alternate seed, retry, or runtime change.

