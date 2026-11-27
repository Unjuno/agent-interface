# Reproduction

Run in Ubuntu WSL with Python 3.12.3 and the local repository containing the frozen commits:

```sh
A07_INPUTS=/mnt/d/codex-research/scratch/v39_cleanup_regression_suite_wslc_a07_20261012/inputs \
A07_RESULTS=/mnt/d/codex-research/scratch/v39_cleanup_regression_suite_wslc_a07_20261012/results \
python3 /mnt/d/codex-research/scratch/v39_cleanup_regression_suite_wslc_a07_20261012/runner/run_suite.py
A07_GIT_REPO=/path/to/agent-interface python3 /mnt/d/codex-research/scratch/v39_cleanup_regression_suite_wslc_a07_20261012/audit.py
```

The runner executes the PR test module against both source modules in normal and optimized mode and asserts which source module Python imported. The independent audit checks Git blob IDs and the raw test transcripts. Re-running the unit tests is not needed to validate the retained result.

No model, game, GUI, OS input or GPU was involved. This package is construction/regression evidence only.

