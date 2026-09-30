# #2624 V2 publication bundle audit — 2026-09-28

## Disposition

**HOLD_EVIDENCE_SEGMENT_GAP.** The GitHub branch records a scoped PASS claim, but its published evidence bundle cannot currently be reconstructed from the published members. This audit does not invalidate or relabel the original scientific allocation; it limits independent reproduction/publication completeness. The V2 allocation itself was not rerun.

## Local Docker method

Audited the four published base64 evidence segments and manifest from branch `research/mindustry-live-smoke-orientation-2624-20260926`. All four present segment byte streams were checked against GitHub Git-blob SHA-1 identities. The manifest declares 36 raw archive members.

Executed locally with Docker Desktop, image `python:3.12-slim-bookworm` (linux/amd64; image ID `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`). Container had `--network none`, read-only root and source mounts, 0.25 CPU, 512 MiB RAM, 64 PID cap; only a fresh output directory was writable. This was a posthoc publication-integrity audit only, not a scientific-session rerun.

Command ran `python /src/audit_publication_bundle.py`; exit code **2**, the expected non-pass HOLD exit. The exact JSON output is retained in [LOCAL_AUDIT.json](LOCAL_AUDIT.json), SHA-256 `d054e20010aa8978c7b5f4d7859461fcec9c27f4989757dd37db313d58c3f011`.

## Findings

- Present part indices: 00, 02, 03, 04; required contiguous index **01 is absent**.
- All four present parts match their independently read-back GitHub blob identities.
- The 36-entry manifest therefore cannot yet be checked against a decoded archive; no decompression or member-level completeness claim is possible.
- The frozen source identity inventory also names V2 `run.py` (Git blob `9d45b9480d0f3ed5744a038fc45bba0830e95827`, SHA-256 `65fdbad6f46e03d2e95fc29d78f3c1cb86e19211acf705b9780d61dadce4a9ca`), but the file is absent from the V2 branch.
- Checked the four matching #2624 branches (orientation V2, premounted V1, materialized V1, and acquisition branch); neither `evidence.part01.b64` nor the V2 `run.py` is available at the claimed path. Local scratch/worktrees also contained no matching recovery bytes.

## Interpretation / next action

Keep #2624's original V1 FAIL and V2 scoped PASS records immutable. Do not synthesize the missing archive segment or recreate the missing runner from a hash/report. The V2 claim remains historical evidence, but its GitHub bundle is not independently complete. If original exact bytes are recovered from the allocation owner/archive, verify their hashes and source identities locally in Docker, then publish them additively in a successor delivery branch/PR. Otherwise retain this HOLD and leave the scientific outcome unchanged.

This finding is scoped to publication completeness. It does not claim the Mindustry fixture or V2 experiment failed, and it does not cover gameplay, task correctness, reuse, controller behavior, or economics.
