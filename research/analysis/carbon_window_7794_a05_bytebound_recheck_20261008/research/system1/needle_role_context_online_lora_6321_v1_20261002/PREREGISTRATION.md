# Explicit role context for online Needle LoRA — Issue #6354

Allocation `NEEDLE-ROLE-CONTEXT-ONLINE-LORA-20261002-01`; successor to #6321's preserved pre-fit STOPs. This is a fresh allocation, not a retry or data reuse. Base main at branch creation: `c80e98614720c95dc68a6a48e2d057ae6e94b98e`.

## H

Explicit role identity lets a rank-2 online adapter acquire B behavior while preserving A. A same-base control with role identity held constant cannot disambiguate contradictory A/B targets on the same feature vector.

## T

- Fresh seeds: 2026100204, 2026100205, 2026100206. No #6321 or predecessor raw data, optimizer state, source, or outputs reused.
- Eight binary features. A support 64 (32 per feature0), B arrivals 8 (4 per feature0), A/B heldout 128 each (64 per feature0). Within each role/seed, support/arrival and heldout feature vectors are disjoint; cross-role overlap is intentional. A(x)=0; B(x)=x[0].
- Within each role, support/arrival and held-out vectors are disjoint. Cross-role overlap is intentional and quantified by the auditor; identical inputs may occur across roles. Each seed also carries an explicit role-conflict probe with one identical vector and the two target labels, independently checked against A(x)=0 and B(x)=x[0]. This makes the no-role ambiguity concrete without changing the primary split sizes.
- Model: 9→16 ReLU→4 MLP. A base trained exactly 400 AdamW steps at LR .04 on `[role=0, x]` A-support; then frozen. Two arms share a byte-identical base initialization and data, each with an independently initialized rank-2 output LoRA. Control always presents role=0 on both A/B, uses a shared adapter on both roles, and receives no B identity. Treatment uses role=0 for A and role=1 for B, and applies its adapter only when role=1. Both adapters receive exactly eight sequential one-row AdamW updates at LR .04 from identical B-arrival rows; persistent optimizer state. Measure full heldout A/B before updates and after each of eight updates.
- Scope gate is exercised as a separate proposal-only contract: fresh known scope => PROPOSE; stale, unknown, or intent-mismatched scope => YIELD; dispatch count remains zero. It grants no runtime authority.
- Candidate: WSL 3.0.1 WSLc only; cached image `pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`, linux/amd64, PyTorch 2.5.1/CUDA 12.1. `--pull never --network none --gpus all --cpus 1 --memory 2G --user 65534:65534`, read-only source/input mounts, fresh output mount, `--rm`. WSLc does not expose rootfs read-only; its ephemeral root layer is writable. Kernel warning means swap accounting/enforcement is unavailable. Candidate asserts CUDA and RTX 3080; no CPU fallback.
- One candidate invocation across three seeds and both arms; one separate GPU-disabled/network-disabled stdlib-only auditor only after candidate exit 0; retries=0. No model/provider calls, GUI, user data, dispatch, Docker Desktop, or Podman.

## D

`PASS_ROLE_CONDITIONED_ONLINE_ADAPTATION_SCOPED` only if treatment heldout A accuracy is >=.90 at baseline and every checkpoint and treatment heldout B is >=.90 after update 8 for all three seeds; base weights stay immutable; schedule, data, all predictions and metrics independently replay with zero errors; scope negatives all YIELD with zero dispatch; and every frozen mutation is rejected. Report control trajectories regardless; no control outcome is required to rescue a failed treatment. Any integrity failure is STOP; treatment quality miss is HOLD. No retry, tuning, seed substitution, or threshold change.

## C

The only treatment contrast is task-role observability and adapter gating; both arms share the same A-trained base. Synthetic finite binary inputs are intentionally simple. Feature vectors may overlap across roles, which makes the no-role control's ambiguity observable. One host, one RTX 3080, one framework/image; GPU kernels and single-machine behavior limit generalization.

## U

This does not test natural-language role inference, real-time GUI, a reusable production skill, general continual-learning/forgetting, multi-agent/network integration, authority safety, latency/energy benefit, or product success.

## Resource gate

An exclusive 2026-10-02 01:15–01:45 UTC RTX 3080 WSLc slot is requested on #5085, not granted. No GPU invocation absent an exact owner/allocation/window assignment plus immediate fresh main, image/source/data/output, process/container and overlap checks. Same physical GPU means WSLc/Podman/Docker requests cannot overlap.
