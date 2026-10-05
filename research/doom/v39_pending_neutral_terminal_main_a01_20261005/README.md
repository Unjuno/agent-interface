# V39 pending invalidation with neutral terminal races (construction only)

This experiment composes the current-main V39 paired-health pending-answer invalidation path with the `cancelled`, `completed`, and `expired` cover terminal outcomes accepted by `cancel_invalidated_cover`. The pending planner returns an answer-eligible result after interruption; all three cases require the answer to be rejected by final admission and require independently verified empty keys/buttons before the terminal is accepted.

The controller source is unchanged. No game, model client, GUI, OS input, or formal/live allocation was used. This does not satisfy the current live threat exposure requirement in `docs/CURRENT_GOAL.md` and does not justify a production repair.

Reproduce with Python plus Pillow and NumPy:

```sh
uv run --with pillow --with numpy python -m unittest discover -s research/doom/v39_pending_neutral_terminal_main_a01_20261005 -v
uv run --with pillow --with numpy python -O -m unittest discover -s research/doom/v39_pending_neutral_terminal_main_a01_20261005 -v
```

Both normal and optimized runs pass (one test, three terminal cases). Raw outputs are `raw-normal.json` and `raw-optimized.json`. They bind to controller SHA-256 `f76c618f5eedbe2c301eecb67c36c9064ec0de035009d0be6f8610bb1d808dc8`.
