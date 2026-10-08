# Recovery review — Issue #2881

This recovery publishes the two retained files from the old remote branch so
the construction-only STOP is visible from `main`. It does not claim the T1
hypothesis was tested: the formal invocation count and scientific row count are
both zero.

The report records three successive child/Xvfb teardown-control attempts and
the final excluded science-pair construction failure: Python-Xlib returned
`str` for the progress/harm scoring image, causing the frozen scorer to raise
`TypeError("string argument without an encoding")`. The preserved outcome is
`STOP_CONSTRUCTION_SCORE_IMAGE_STRING8_TYPE`; it is neither PASS nor FAIL on
the T1 hypothesis. No source compatibility repair or formal rerun is implied.

`CONSTRUCTION_HASHES.json` preserves SHA-256 commitments for six
conversation-local construction/diagnostic artifacts. Their original bytes are
not in this branch, so this recovery does not assert that those raw logs are
independently replayable from GitHub alone. The Issue remains the full context
for the one-factor boundary and the requirement for a newly frozen successor
before any future execution.
