# MAP01 explicit action-boundary clock probe — construction only

Disposition: `PASS_CONSTRUCTION_ONLY_EXPLICIT_ACTION_BOUNDARY`; Issue #3453 remains `HOLD_LIVE_SPAN_UNIDENTIFIED`. Formal allocation remains 0/120.

## H / question

On the pinned private MAP01 fixture, does the existing ViZDoom `advance_action(1, True)` boundary make the public episode-tic snapshot progress when called at approximately the requested 35 Hz cadence, and can the unchanged current-main `_coherent_progress_sample` be called after each boundary with its complete getter trace retained? This probes the frozen session API boundary; it is not a phase allocation.

## T / experiment

- OrbStack Docker, Linux/arm64, image `issue-3300-map01-fixture-smoke:v2`, image ID `sha256:8d984b04efe5bca7bd9b3808aac4f56bd273a6a1ada76cd51939253b874244ca`.
- ViZDoom 1.3.0, `ASYNC_SPECTATOR`, requested ticrate 35, fixed private fixture `map01-threat-contact-v2`, MAP01 skill 1, seed 990619. The container used `--network none`; no model, host desktop, OS input, or button vector was used.
- Two fresh game sessions loaded the same immutable fixture save. Both used the predecessor's one-tic startup refresh. Each then sampled 20 times against 28,571,429 ns targets. Condition A waited passively; condition B called the existing `game.advance_action(1, True)` once per target. The exact current-main `_coherent_progress_sample` was called once after each sample/boundary. A tracing proxy retained all eight scorer getter calls and monotonic start/end timestamps.
- Container runtime initialized Xvfb and Openbox before the Python probe. An earlier launch overriding the image entrypoint without starting Xvfb stopped before game initialization (`SDL: No available video device`); it produced no scientific rows and was not counted.

## D / independently audited observations

Independent stdlib audit: `PASS_CONSTRUCTION_ONLY_EXPLICIT_ACTION_BOUNDARY`, 40 rows, zero audit errors. Each condition initialized and closed cleanly; every scorer trace had the exact eight-getter order, same-tic before/after bracket, and independently reconstructed result fields.

| Condition | Samples | Initial → final public tic | Per-boundary tic delta | Scorer span |
|---|---:|---:|---|---:|
| Passive wait | 20 | 1367 → 1367 | 0 on 20/20 | median 58.79 µs; range 38.75–178.21 µs |
| `advance_action(1, True)` paced at ~35 Hz | 20 | 1367 → 1388 | 1 on 19/20, 2 on 1/20 | median 60.35 µs; range 45.00–100.38 µs |

The driven block's net public-tic delta was 21 over 600.764 ms to the final sample (34.955 tic/s). The action-call wall spans were 2.961–41.002 ms. One additional tic beyond the 20 requested action tics is visible in the public snapshot; its exact origin is not identified here.

## C / scope and inference boundary

This confirms that the existing explicit action-boundary call can expose advancing tic snapshots on this fixture, while passive Python reads remain static. It does **not** establish that async gameplay progresses autonomously, supply an independent/non-perturbing engine-edge clock, estimate scorer phase relative to a live edge, establish three-attempt failure probability, or meet the frozen `ASYNC_SPECTATOR` formal estimand. In particular, using `advance_action` as the repeated driver may alter the measurement boundary and cannot be silently substituted into the one-shot 120-row allocation. Do not pool these 40 construction rows into formal results.

The result narrows the next question: determine from the frozen MAP01 live-session contract whether the intended clock-driving boundary is this repeated action call or an independent async engine source, then validate an independent witness without adding actions to formal scorer intervals. Until that is resolved, keep `HOLD_LIVE_SPAN_UNIDENTIFIED` and do not freeze/start formal collection.

## U / artifacts and hashes

- Raw full trace: `raw.json`, SHA-256 `0abb28cca7b6e8a6d92ebe6923ee49cf067952593c7cae39220337059d461819`.
- Independent audit: `audit.json`, SHA-256 `565a83fbd6224494cd3494f4c00328fbbbed15e5a432982bf19550c09f049f45`.
- Runner: `map01_clock_drive_probe.py`, SHA-256 `86cc32e098738e3f5c3a52d823a9f8b27e60fd1d9ccd683590a8c64d0365191d`.
- Auditor: `audit_map01_clock_drive_probe.py`, SHA-256 `59f827ef9fe73fbb0a70546f35d1f442dd6ebb8403e24eca9bf59754eb8a33a3`.
- Exact in-image session/scorer sources: `session_map01_v13.py` SHA-256 `1a6da676db9c6b2aa61ccf0f600a1565395e906736bb07a50b2006e100d7ca98`; `independent_progress_clock_v2.py` SHA-256 `3d906a7043f0d674bac3bd137952adeac11c77c9339bc38ef6ca37b05e0d1613`; `map01_scorer_stdio_adapter_v1.py` SHA-256 `0ba57b240b37d04042915d243d149a1bb65ac689732dfc8e48fb60e880f0198a`.
- Fixture manifest `e57e21fd6d85d4b0720b3b3d5a52ad538fde45c50c58651ff754638f93f182e`; save `cc5302aa9cda3960248733caa96da1b53adcc4b6a1a2dcfb80675650c9350401`; Freedoom WAD `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.

The audit recomputes trace order, tic brackets, returned result fields, drive/scorer spans, row counts, and cleanup from raw JSON; it does not import the runner or scorer implementation.
