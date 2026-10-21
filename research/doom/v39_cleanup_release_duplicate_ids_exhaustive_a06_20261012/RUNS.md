# Reproduction

Run in Ubuntu WSL (Python 3.12.3), from a clean copy of this package:

```sh
python3 candidate.py
python3 audit.py
```

Both commands should exit 0 and write `results/candidate.json` and `results/audit.json`. The auditor uses the local Git repository at `/mnt/d/codex-research/issue59-stale-replan-pr-20261008` to check the two frozen source blob IDs. For another checkout, set `A06_GIT_REPO` to its path after verifying the same commit and blob identities.

No container, network access, model, GUI, OS input, or game process is involved.

