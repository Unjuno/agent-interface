# Issue #4799 — fixed experiment source (pre-formal)

## Frozen H/T/D/C/U

- **H:** A tiny learned gate can suppress clear irrelevant changes in source-bound X11 pixels from wholly held-out layout families while forwarding every task-relevant/critical change. Missing, stale, or ambiguous provenance yields before model inference.
- **T:** Capture 120 ordered before/after pairs from six Tk windows rendered on Xvfb (320×240, native XGetImage/X.ZPixmap bytes). Families 0–3 (80 pairs) are train-only; families 4–5 (40 pairs) are whole-family held out and use different palette/geometry. Each family has 8 irrelevant, 8 task-relevant, 4 critical updates. Train one CPU model, one seed, one fit/eval; then a separate standard-library-only raw audit.
- **D:** Scoped pass iff zero held-out task/critical false suppressions; at least 8/16 clear irrelevant held-out pairs suppressed; every critical, missing, stale and unknown-format case forwards/yields; raw hash, exact-region O3 labels, source split, threshold, and mutation checks pass. Else FAIL on unsafe suppression, HOLD on safe but low utility/audit, STOP on unavailable pinned image/X11 prerequisite.
- **C:** No package install/network/host GPU/runtime use. Capture image `codex-x11-preflight:local`, expected ID `sha256:a27c1782065d2240547482d4e0327d54b1a58cf3e45bf0a0326115822337c48a`. Fit image `pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime`, expected ID `sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`. Both local linux/amd64; containers network-disabled, read-only root, 1 CPU, bounded memory, dataset/source read-only; only dedicated output mount writable. Fit CPU-only, `CUDA_VISIBLE_DEVICES=''`, one Torch thread.
- **U:** Authored synthetic Tk/X11 fixtures only; one seed, six families, 120 pairs. No real-app transfer, arbitrary visual semantics, task success, runtime authority, deployment, or performance claim.

## Frozen source and invocation

This directory's `capture_x11.py`, `train_eval.py`, `audit.py`, and this document must be committed on the unique research branch and read back byte-for-byte before data capture. Record the commit and Git blob IDs in the formal report. Do not edit these files after capture. Output is kept outside the repository during execution; only compact, lossless source pixels, machine-readable decisions, checksums, and a report are eligible for the result commit.

1. Start a fresh Xvfb display inside the pinned capture image and run `capture_x11.py` exactly once with a new empty output directory.
2. Read back and verify all capture SHA-256 values. Run `train_eval.py` exactly once in the pinned PyTorch image, using `DATA_DIR` read-only and a new empty result directory. No CUDA device is passed.
3. Run `audit.py` once in a separate network-disabled Python standard-library container with capture and fit inputs read-only and an empty output directory.

No retries, tuning, alternate seeds, threshold changes, or substitute images after the formal run begins. A failed run is retained and classified; any materially revised design gets a successor issue.

## Model definition

Input channels are max-pooled 32×32 exact XGetImage per-pixel byte deltas plus the declared task ROI mask. The CPU CNN is Conv(2→4, 3×3), ReLU, Conv(4→4, 3×3), ReLU, adaptive max pool, and Linear(4→2); 194 trainable parameters. Seed 2188, Adam(lr=0.01), 120 full-batch steps, cross entropy. Suppress only if irrelevant probability ≥0.98; critical ROI overrides with FULL_FORWARD. This is an offline experiment, not a runtime gate.

## Provenance boundaries

Fixture windows are newly authored by this experiment and have no user data. The raw audit independently hashes/decompresses source frames and computes exact changed-pixel/task-ROI intersections (O3 comparator). The train/test partition is by entire family before capture. Every missing frame, sequence mismatch, or unsupported pixel format must YIELD. Raw captures can only establish behavior on these six constructed layouts.

