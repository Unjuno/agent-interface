# Issue #4588 — formal result

**Disposition: `HOLD_NOISE_AMPLIFICATION`.** The audit has zero integrity errors, but no temporal arm passed the frozen safety/utility gates. No run was repeated and no parameter or threshold was tuned after observing this outcome.

## Execution and integrity

- One frozen orchestration; runner and independent auditor each ran once in separate local Docker containers; both returned 0. Retries/tuning: 0.
- Ten seeds; per seed, 1,760 train + 880 validation + 880 held-out test rows; validation was diagnostic only. Four arms used the same linear-head shape, seed initialization, optimizer/schedule and data; only feature masks differed.
- 8,800 held-out rows total. Independent stdlib auditor regenerated all splits, recalculated logits/predictions/metrics and checked source/evidence hashes: **0 errors**.
- Pinned `needle-pilot05:local`, image `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`; CPU-only, no network, read-only root/source, 1 CPU, 2 GiB, 64 PIDs, one torch thread. PyTorch emitted a missing-NumPy warning; no package was installed.

## Held-out comparison

| Arm | Accuracy | False-executable rate | Unnecessary ACTION on true NO_OP |
|---|---:|---:|---:|
| CURRENT_ONLY | 75.50% | 26.38% | 23.33% |
| LEVEL + VELOCITY | 80.94% | 28.52% | 33.33% |
| LEVEL + VELOCITY + ACCELERATION | 81.97% | 28.32% | 33.33% |
| CAUSAL_SMOOTHED | 82.00% | 26.84% | 30.00% |

The acceleration arm gained 6.47 percentage points in overall accuracy over current-only, but false-executable rate rose by 1.95 points (about 109 additional false executable decisions over the 5,600 non-executable test rows), while unnecessary actions on NO_OP rows rose by 10 points (240 additional actions over 2,400 NO_OP rows). It therefore fails the preregistered safety gates despite higher accuracy.

On the deliberately aliased subset (1,600 rows; 800 non-executable): CURRENT_ONLY scored 35.0% accuracy and 70% false-executable rate; velocity and acceleration each scored 50% accuracy but 100% false-executable; causal smoothing scored 50% accuracy and 90% false-executable. Thus none separated useful action from NO_OP safely; the acceleration arm also did not beat velocity by 5 points.

Hard fail-closed handling for stale/missing/epoch-mismatched histories passed 100%, and false-NO_OP on required-action rows was 0%. The noisy/irregular accuracy tolerance passed, but false-executable non-increase failed overall. Outcome is a negative safety/utility result, not evidence to promote trajectory-conditioned action selection.

## Descriptive CPU timing

Across 8,800 single-row in-container inference calls per arm, p95 was 0.00479 ms (CURRENT_ONLY), 0.00473 ms (LEVEL+VELOCITY), 0.00483 ms (LEVEL+VELOCITY+ACCELERATION), and 0.00481 ms (CAUSAL_SMOOTHED). These tiny synthetic linear-head measurements are descriptive only and do not establish end-to-end or production real-time performance.

Raw per-seed JSON evidence is preserved under `outputs/formal01/training/seed-*` and losslessly bundled under `outputs/formal01/bundles/`; `EVIDENCE_MANIFEST.json` records each ZIP and raw-document SHA-256. The repository branch carries the formal report, audit, summary and bundle manifest. Binary ZIPs remain in the task workspace because the connected GitHub writer accepts UTF-8 text files only.
