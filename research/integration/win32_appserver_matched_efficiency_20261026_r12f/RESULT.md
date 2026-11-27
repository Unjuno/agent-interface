# R12f result — independent Win32 matched replication

**Classification:** `PASS_SCOPED_COUNTERBALANCED_WIN32_MATCHED_STUDY`  
**Source:** `cc42df79f4c6dbef2e9457d3dae31663e7368f31`  
**Runtime:** Python 3.13.14; Codex App Server `gpt-6.1-sol`, low effort  
**Audit:** `AUDIT.json`; all four cells, cell hashes, pretrial hashes and run hashes pass.

R12f repeats R12e's fixed local task with four new fixtures and oracle IDs. Its order is direct→compiled, then compiled→direct. All cells passed exact task effect, same-generation observation, release, native all-up, independent terminal oracle, and fixture/App Server/foreground cleanup checks. The compiled method performed two locally verified transitions after the same initial model-grounded click choice.

| Pair/order | Arm | Total elapsed | App Server time | Provider turns | Reported input/output tokens | Observations / dispatches |
|---|---|---:|---:|---:|---:|---:|
| 1, direct first | Direct | 8.589 s | 7.073 s | 2 | 20,737 / 34 | 5 / 2 |
| 1, direct first | Compiled | 6.144 s | 4.628 s | 1 | 10,255 / 19 | 4 / 2 |
| 2, compiled first | Compiled | 5.437 s | 3.917 s | 1 | 10,255 / 19 | 4 / 2 |
| 2, compiled first | Direct | 9.511 s | 7.964 s | 2 | 20,737 / 34 | 5 / 2 |

Direct-minus-compiled total elapsed was +2.445 s and +4.075 s; App Server time differences were +2.445 s and +4.048 s. Each pair used one extra direct provider turn, +10,482 reported input and +15 output tokens, and one extra public observation. Both arms dispatched two actions and passed the same exact task oracle.

## Combined R12e/R12f block

Across four counterbalanced pairs (n=4 per arm), all eight cells passed. Every paired difference favored compiled on elapsed and App Server time. Median direct-minus-compiled differences were **+3.425 s total** and **+3.419 s App Server time**. Direct used two model turns/five observations per cell; compiled used one turn/four observations. Both used two dispatches. The first block's full cell table and setup failures are in [R12e](../win32_appserver_matched_efficiency_20261026_r12e/RESULT.md); R12–R12d failures remain immutable.

This is a replicated descriptive result for one owned fixture task on one PC. Four successful cells per arm do not establish general reliability or a causal efficiency effect. App Server token counts are protocol-reported usage, not independent billing evidence; image-token accounting is unavailable. No WSLc, Docker, production game, or MAP01/live-GUI execution is established. Raw data and SHA-256 manifests remain in `run/` and the per-cell folders.
