# V39 pending invalidation with neutral terminal races (construction only)

This experiment composes the current-main V39 paired-health pending-answer invalidation path with the `cancelled`, `completed`, and `expired` cover terminal outcomes accepted by `cancel_invalidated_cover`. The pending planner returns an answer-eligible result after interruption; all three cases require the answer to be rejected by final admission and require independently verified empty keys/buttons before the terminal is accepted.

The controller source is unchanged. No game, model client, GUI, OS input, or formal/live allocation was used. This does not satisfy the current live threat exposure requirement in `docs/CURRENT_GOAL.md` and does not justify a production repair.

Reproduce with Python plus Pillow and NumPy:

```sh
uv run --with pillow --with numpy python -m unittest discover -s research/doom/v39_pending_neutral_terminal_main_a01_20261005 -v
uv run --with pillow --with numpy python -O -m unittest discover -s research/doom/v39_pending_neutral_terminal_main_a01_20261005 -v
```

Both normal and optimized runs pass (one test, three terminal cases). Raw outputs are `raw-normal.json` and `raw-optimized.json`. They bind to controller SHA-256 `f76c618f5eedbe2c301eecb67c36c9064ec0de035009d0be6f8610bb1d808dc8`.

## Posthoc guard-threshold sensitivity

The retained Astra HUD analysis records a manually transcribed 84 → 77 → 84 health trace during one model wait. This controller did not consume the intermediate video frame, and the retained answer has no authored validity policy for it. A separate deterministic sensitivity check feeds those values to the current V39 `build_cover_monitor` under candidate authored bounds. It sweeps `maximum_health_loss` 0–20 at `critical_health_minimum=35`, plus critical-minimum edge values 35, 77, 78 and 84 at loss 12.

The check shows the implementation's strict floor: it invalidates at 77 only if `max(critical_health_minimum, 84 - maximum_health_loss) > 77`. Thus loss ≤6 or critical minimum ≥78 interrupts; equality at 77 (loss 7 / critical minimum 77) is a soft change and preserves the existing cover. The first observation of this arithmetic preceded packaging the reproducible sweep; this is posthoc threshold sensitivity, not a preregistered allocation or evidence that any model actually authored those bounds.

The additional test reads the retained, hash-pinned `astra_continuous_hud_a01/result.json`, binds the exact current controller source, and writes `raw-health-sensitivity-normal.json` and `raw-health-sensitivity-optimized.json`. This informs which guard conditions the next fresh live exposure should retain; it does not qualify a threshold, infer threat cause, or establish controller response, survival, or task effect.
