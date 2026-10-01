# v9 formal allocation freeze — seed 990635

Issue: [#4484](https://github.com/Unjuno/agent-interface/issues/4484)

## H/T/D/C/U

- **H:** With the required hash-bound Freedoom WAD restored and its health/ammo readers verified, the frozen guarded controller can enter MAP01 and admit multiple bounded model-authored actions under currently available model usage.
- **T:** One new formal OrbStack run, fresh MAP01, skill 1, seed `990635`, maximum 24 decisions, `gpt-5.6-luna`/low, session span 4, pinned image, visible-only observations, bounded OS input, independent score.
- **D:** PASS only for independently scored exit with complete clock/input/provenance/release gates. FAIL only for a complete interpretable 24-decision run with real admitted model actions and no exit. Usage truncation/incomplete action evidence is HOLD. Setup/release failures are STOP; no retry.
- **C:** Issue #4484 is the one-time preregistration. Local and GitHub open/closed issue, all-state PR, branch and path collision searches found no prior claimant for seed `990635` or the v9 output path. Current main before this freeze is `5dd2b9b18fc5f3e73e8ff9adf808806a49a121ce`; all 20 frozen runtime input files were blob-hash compared and match current main. Preserve #4473/v8 and v1-v7 unchanged. Do not run while unrelated OrbStack container `cans-updated-build` is active.
- **U:** Whether the full controller reaches gameplay; whether the model allowance sustains all decisions; whether admitted actions make progress or exit MAP01.

## Exact invocation (frozen; invoked once)

```sh
env PYTHONDONTWRITEBYTECODE=1 /Users/taka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B research/doom/map01_model_loop_finite_v7/adapter.py --out research/doom/map01_model_loop_finite_v9/results/map01-model-loop-finite-v9-20260926-01 --iterations 24 --seed 990635 --session-span 4 --model gpt-5.6-luna --effort low
```

Output path was confirmed absent before launch. It is now consumed; never rerun this command or reuse the seed/path.

## Frozen identities

- v7 adapter SHA-256: `a92be1f3dbfc8c64f58287188d75db6081987245c9267791b7de05a69d7d6447`.
- Effective controller SHA-256, independently regenerated with `--prepare-only`: `edd4cea89c541d42457e8c48992d3efe1bcb0ab7610489b47e8efa60660aab3a` (64 hex characters; the #4484 issue body omitted the final `a`, now recorded as a preregistration typo).
- v7 source manifest SHA-256: `3bb0fe420f21b682c5739d1e6d1e0ae6996847fceaa5818f0f17a3219437c5f8`; its 20 runtime source inputs match current main as of the commit above.
- Runtime image: `issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e`, linux/arm64.
- WAD: `FREEDOOM2_SHA256=a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`, 28,787,748 bytes. Restored from the pinned image to `/tmp/issue2679-orbstack-preflight/freedoom2.wad`; health and ammo reader initialization passed in a separate no-network, read-only pinned-image preflight (see v8 `preflight/WAD_RESTORE_AUDIT.md`).
- Account usage check at preregistration: ordinary model usage allowed, 5% of the weekly window used; no reset credit consumed.

## Invocation gate and preservation

Immediately before launching, recheck latest main and the 20 source hashes, issue/PR/branch/path/seed claims, output-path absence, model usage, WAD path/hash, and OrbStack containers. The unrelated high-load container must have exited; never inspect beyond status/resource metadata, stop, or mutate it. Once all gates pass, invoke exactly once. Preserve raw output and audit it read-only; never reuse this seed or path.

## Post-allocation addendum

- Launch: 2026-09-26; Issue #4484; main source comparison at launch: `74ad7e3afc5ddbf43e3544d86780a210012ced34`; all 20 source SHA-256 values still matched the freeze manifest.
- Current Codex usage at launch: ordinary usage allowed, 9% of weekly usage consumed; no reset credit was used.
- Outcome: `HOLD_INFRASTRUCTURE_HOST_LEASE_MARGIN_BELOW_5S` after two model-authored actions. The 5-second observe-only contingency refresh conflicts with the wrapper's strict 5-second remaining-margin gate. Nine of nine owner releases verified empty; no final score or 24-decision result exists.
- Preregistration discrepancy: #4484's effective-controller digest text was 63 characters and malformed as SHA-256. The frozen v7 record and generated effective source agree on the 64-character digest ending in `a`; the exact adapter and source manifest were frozen and match. Preserve this issue-body typo; do not rewrite the historical preregistration.
- Full immutable evidence and scope limits: `results/map01-model-loop-finite-v9-20260926-01/STOP_RECORD.md`; read-only audit: `results/map01-model-loop-finite-v9-20260926-01/V9_STOP_AUDIT.json`.
