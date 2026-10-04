# Independent reconstruction of sampled game-action trace — A01

**Disposition:** `PASS_SAMPLED_GAME_ACTION_STATE_SCOPED` and `STOP_PROTOCOL_COMPLETION`, independently reconstructed from the committed raw trace. No game, model, input, GUI, or container was rerun.

## H/T/D/C/U

- **H:** The retained scorer-only `get_last_action()` stream independently identifies sampled OS-key state for one submitted `Left` hold, while the surrounding episode/protocol record determines whether the construction completed normally and whether the samples establish useful recovery.
- **T:** A new raw-only auditor reads the exact #7599 construction-03 bytes from commit `fe5a9dddf11f0351eb65001f1a1ddb867e8a5012`. It independently parses action samples, runtime events, scorer progress samples, environment configuration and the final outer-probe status; it does not import the original runner or reuse `SAVED_ACTION_AUDIT.json` as an oracle. Five mutation controls check that identity, sample, release and STOP corruptions are rejected.
- **D:** The 717-row action stream has 717 coherent tic brackets. Exactly eight samples report only `TURN_LEFT=1`, at tics 1375, 1376, 1377, 1379–1383. The nearest earlier neutral sample is tic 1374; the first later neutral sample is tic 1384. Tic 1378 has no sample, so uninterrupted per-tic occupancy is not established. The eight sampled active values follow the matching `Left` admission/held events and precede an identity-matched owner `KeyRelease`/`XSync` bracket; the first neutral sample follows it. The separate scorer stream contains 715 rows with zero kills/deaths and no map exit. The environment exposes only `DEATHCOUNT`/`KILLCOUNT`, so damage and ammunition change are unmeasured. Although the inner program emitted a completed terminal event, the outer probe ends with child exit `-9`, an alive reader and external rescue; the unsupported top-level coast command was rejected. Protocol completion is STOP, not PASS.
- **C:** This is one source-scoped sampled game-side state observation, not an exact engine transition timestamp, continuous tic-by-tic occupancy, physical release verification, useful task feedback, combat effect, matched recovery benefit, or normal session shutdown. The score channel does not expose damage or ammo in this construction.
- **Review status:** The raw-only checker is a separate implementation from the original post-result summary, but it was produced by the same worker. Independent external review of this reconstruction remains pending.
- **U:** Keep this trace as a bounded input-state result and its protocol STOP. The next comparison must use a newly frozen construction with a submit-contained coast, retain a common measurement window before cleanup, and independently score progress/damage under matched conditions. Do not rerun this Left construction or treat these rows as recovery evidence.

## Reproduction

From this directory, run:

```powershell
python -B audit_raw.py
python -B -m unittest -v
```

The first command emits `AUDIT.json`; the second emits `TEST_OUTPUT.txt`. Both read the committed raw files from the pinned Git commit named in `FREEZE.json`. They never initialize ViZDoom or send input.

## Provenance

- Original source commit: `fe5a9dddf11f0351eb65001f1a1ddb867e8a5012` (merged #7599).
- Original retained package: `research/doom/game_action_sampling_59_4d74_20261004/construction03/`.
- Input file SHA-256 pins are in `FREEZE.json`; output package hashes are in `FILES.sha256.json`.
- This audit does not replace the original construction's retained PASS/STOP labels or its host/container evidence.
