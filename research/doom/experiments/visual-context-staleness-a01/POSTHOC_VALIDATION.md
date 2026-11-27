# Post-run construction and evidence audit

This is a local post-run check of the retained A01 bytes. It did not invoke
WSLc, the game, a model, or the input executor and does not count as a second
formal allocation.

On Windows CPython 3.11.9 with Pillow 10.2.0:

- `python -m unittest -v test_visual_context_staleness_v2`: 2/2 synthetic
  cases passed. The corrected test writes runtime prompt text under a temporary
  directory and verifies that the frozen `prompt.txt` hash is unchanged.
- `python audit_visual_context_v2.py`: passed. It verifies manifest and frozen
  source/input hashes, recomputes both decoded RGB hashes from the PNG bytes,
  confirms fixture/raw-event agreement, parses the two result records from the
  retained WSLc transcript, and requires exact equality with `result.json`.

The original v1 test, freeze, WSLc transcript, result and audit are retained.
This follow-up does not upgrade the experiment beyond its scoped software
boundary characterization and does not establish a threat, live control effect,
physical release, recovery, or task success.
