# Issue #2447 — paired visual-effect construction result

Disposition: **PASS_CONSTRUCTION_INSTRUMENTATION**, one new episode only. This verifies that fresh pre-action and post-release screen evidence is retained and independently measurable for both bounded turn subgoals. It is not Issue #2447 acceptance, comparative efficacy, or a MAP01 completion result.

## H/T/D/C/U outcome

- **H:** Supported at the instrumentation boundary. Paired screenshots made both Right and Left turn effects independently measurable from pixels; hidden scorer yaw was not used by the visual-flow auditor.
- **T:** One Docker Desktop Linux/amd64 episode, seed `2447006`, drop class, temporal gate, requested setup heading `110°` (actual `103.71094°`, within the inherited <8° setup tolerance), then Right 190ms and Left 190ms. The runner was copied additively and changed only to retain the pre-action image and post-release/engine-sample image plus sample timestamps. The inherited frozen runner and prior case were not edited.
- **D:** Frozen gates passed: all four images exist; each pre-image RGB hash matches its fresh handoff receipt; X11 focus/surface/geometry matches setup; observation/action/release/post-image order is monotonic; both releases are verified empty; independent LK has >=80 valid tracks for both turns. The pinned-container audit reports `errors=[]`.
- **C:** Pinned image `agent-interface-map01-lab:2447-preflight-20260927`, ID `sha256:b99a3444e7b2b05d159976d9ba60d9e90f212d47406c4b7aa7773e5042a28713`, Linux/amd64, network none, read-only root and source, one fresh output directory. No model. Formal rows 0; retries 0.
- **U:** Single temporal-arm episode. No endpoint comparison or fail-closed arm; no injected stale/ambiguous/missing evidence, dropped/delayed frames, false/repeated completion, wrong-direction, focus loss, timeout, restart/recovery, held-out sequence transfer, rate estimate, cumulative episode completion, or product/runtime claim.

## Independent measurements

- Phase LK recomputation over the retained frames: 8 eligible pairs; DROP_COMPLETED at pair indices 6→7. Scorer corroboration: sector 165/Z=-64 to sector 36/Z=-128. A prior inherited v5 audit returned `independent_drop_effect` because it hard-coded destination sector 38; that unchanged failure is preserved. Audit v8 re-evaluates the frozen new-plan requirement as leaving sector 165 and reaching Z<=-120, not a specific landing sector.
- Right: fresh-bound pre-image hash matches; 223 tracks; median dx=-80.1384px, dy=-0.2803px; empty verified release; ordered post-image.
- Left: fresh-bound pre-image hash matches; 210 tracks; median dx=+69.4159px, dy=+0.0668px; empty verified release; ordered post-image.

The v7 runner/auditor source hashes were checked against `FROZEN.json` before the game started. Audit v8 is explicitly posthoc and did not change or rerun the frozen episode. Raw score, source logs, frames, paired turn images and releases are retained under `evidence/issue2447-visual-effects-construction-2447006/`.

## Exact invocation

The pre-run frozen command and artifact identities are in `FROZEN.json`. Its Docker invocation extracts the SHA-256-pinned offline source bundle into `/tmp/project` and runs `src/run_case.py` once with seed 2447006, `temporal_gate`, heading 110. The independent audit invocation is `python /study/src/audit_v8.py --evidence /evidence --out /tmp/AUDIT_V8.json`, with source/evidence mounted read-only, network disabled, and container root read-only.

## Retained artifact integrity

- Raw evidence: 36 files / 1,893,157 bytes.
- Lossless raw ZIP `seq-2447006.zip`: 1,867,094 bytes, SHA-256 `7675d753a5d98e471e42abb1f3c8c81e2c5efa0e1e8f9fb6e9b4c11aac9ba5c3`.
- Raw manifest `evidence-manifest.json`: SHA-256 `b01654039c7d8e5451852852c58cae50774def132448c3d9006445167ccc8dc1`.
- Runner SHA-256 `6acd0f71408d81ea0b0b07e05b4018963d7f918c1ea9446f8a2058afdaa049ea`; frozen v7 auditor SHA-256 `d0300acafaa501bf22c83423a8b7ec19b355bfb6da41871c5fd5c50c04b376f7`; posthoc v8 auditor SHA-256 `cc8997f35dc6e4dd11f00026b807bd010bf25c7ee563e3196cbed068a45ec9ff`.
- The exact raw archive remains separate from the previous case's 33-file archive and is not pooled with it.
- A separate network-disabled Docker stdlib verifier reopened the ZIP and reconciled all 36 entries against the manifest (sizes and SHA-256): `PASS_EXACT_ARCHIVE_MANIFEST_RECONCILIATION`, errors=[]; result is `ZIP_AUDIT_POSTHOC.json`.
