# Reproduction

Use Windows WSLc 3.0.1.0. The run has already been executed once; do not rerun this construction result.

1. Build from `INPUT/` using the pinned base in `INPUT/Containerfile` and tag `a17-pending-ammo-recovery:20261013-r2`. Retained build output is `image-build.log`; retained identity is `image-inspect.json` and `INPUT/FREEZE.json`.
2. The exact candidate command is in `CANDIDATE_COMMAND.txt`. Network was disabled; one CPU and 512 MiB were requested.
3. Candidate output and exit status are in `results/a17-r2/`. Compare the independent audit there.

The WSLc host warned cgroup/swap limit support is unavailable; no memory enforcement claim is made.
