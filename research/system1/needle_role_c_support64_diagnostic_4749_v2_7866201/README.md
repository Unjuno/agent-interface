# Diagnostic successor to #4767 — seed 7866201

This was one paired, synthetic role-C support-count diagnostic, not a repeat of any consumed allocation and not a replacement for #4749's completed ten-seed result. It stopped before model construction because the wrapper's raw-byte serialization raised a TypeError. See `STOP_REPORT.md`; no score exists.

## Provenance

`upstream_runner.py` is byte-for-byte GitHub main's `research/system1/needle_role_skill_c_support64_4749_v1/source/runner.py` (Git blob SHA-1 `ecd3a0414178f38535406573314793a40b353878`). `paired.py` is the one-shot paired orchestration. `audit.py` imports neither runner nor orchestration and reconstructs predictions from raw tensors and inputs.

Seed 7866201 is unique to Issue #4848. The support streams use seed+3. The prefix gate independently invokes the public `data(16, seed+3)` generator and compares exact tensor values/bytes to the first 16 rows of `data(64, seed+3)` before any optimizer updates.

## Execution

Construction: verify frozen source Git blob, parse orchestration, and validate 64-vs-16 exact prefix in the pinned Docker image. Training updates: zero.

Formal: one invocation in `needle-pilot05:local`, image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, `linux/amd64`, `--pull=never --network none --read-only --cpus=1 --memory=2g --pids-limit=64`; source bind read-only, output on a fresh dedicated volume. Base 400 updates; B 120; C each arm 120. No retries.

Independent audit: separate CPU container, network none, root read-only, raw output read-only; reconstruct six role predictions and labels without importing trainer. It checks seed/source identity, data prefix, arm labels, exact A/B parity, reported accuracies/delta.

## Scope

Even a future clean positive result is one descriptive synthetic seed. It does not show realtime online learning, live Astra supervision, role-network transfer to GUI tasks, concurrency, natural-skill transfer, production readiness, or action authority. See `STOP_REPORT.md` for the outcome and exact limitations.

