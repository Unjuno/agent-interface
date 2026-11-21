# Current-main Win32 fixture delayed-effect recheck R01

Status: `FAIL_NO_TASK_EFFECT`; the original public action was not delivered. This is not GZDoom/MAP01 and not an efficiency comparison.

## Result

- Source checkout: Windows main `6d15df538cff4467a6c72a84a93cfc4557917551`; runtime tree matched fetched main before the run.
- One `supervised-win32` action, operation `1ec97b426fa34de8a070d913e73b8c6d`, call `1bf65aa1a587495a8463e9c18c3b16db`.
- Public result remained `UNKNOWN`; `input_dispatched=null`, `task_success=null`, `replay_allowed=false`. No retry occurred.
- Producer packet reported `execution_failed`, detail `invalid program operation receipt buffer`, `backend_emissions=0`, `program_emissions=0`. The parent separately retained three `not_started` operation receipts and emission lower bound 0. These do not explain the child backend error; cause remains unresolved.
- Fixture's recorded application event log contains only `ready`; no keydown or delayed effect was observed and no `effect.json` exists.
- The first automatic recovery was refused because the fixture was not foreground. After recording exact producer absence and restoring focus to this run-owned fixture, one separate `recover_orphaned_input` succeeded: one virtual-key A UP `SendInput` returned, neutral readback reported no down/unknown keys/buttons, and a 2,000 ms late-input horizon was verified (77 samples; largest observed gap 32 ms). This was recovery only; source action stayed UNKNOWN and replay remained forbidden. The fixture event log did not record the recovery key-up.
- The recovery session closed. The run-owned fixture window was later closed through its GUI close control and disappeared from the UI inventory; PID 45488 was absent on final process check. A fixture exit code was not retained.

## Interpretation

This is negative product-path evidence plus one positive bounded recovery observation. It does not establish an end-to-end successful task, MAP01 coverage, provider/model efficiency, or general recovery reliability. The backend error needs separate root-cause diagnosis and a fresh independent run; this run must not be replayed.

## Evidence

See `conditions.json`, `COMMANDS.md`, `source/`, and `raw/`. `raw/final-verification.json` records final observed custody, fixture, and effect state. Recovery transaction results are in `raw/recovery-r03/`; the prior focus-mismatch refusal is in `raw/recovery-r02/`.
