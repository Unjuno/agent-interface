# Frozen container commands (not yet invoked)

Allocation `stigmergic-coordination-5346-t0-20260930-01`; exact CPU slot must be
granted in #5085 first. Run from a clean current-main checkout on a quiet host
and recheck `docker ps`, image ID, branch/source hashes, and lease window
immediately before invocation.

Image: `python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b`
(locally cached; inspect verified `linux/arm64`). Source is read-only; output is
the only writable mount. `--pull=never` and `--network=none` forbid image/network
changes. Resolve the paths in the checkout containing this package and create
the empty output directory:

```sh
REPO_ROOT="$(git rev-parse --show-toplevel)"
STUDY_DIR="$REPO_ROOT/research/analysis/stigmergic_coordination_5346_t0_v1"
RESULT_DIR="$STUDY_DIR/results/formal-01"
mkdir -p "$RESULT_DIR"
```

The exact one-shot invocation is:

```sh
docker run --rm --pull=never --platform linux/arm64 --network=none --read-only \
  --pids-limit=64 --cpus=1 --memory=512m \
  --mount type=bind,src="$STUDY_DIR",dst=/study,readonly \
  --mount type=bind,src="$RESULT_DIR",dst=/out \
  python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b \
  python -B /study/run.py /out/raw.json
```

Only if that exits zero, run the separate raw-only audit once:

```sh
docker run --rm --pull=never --platform linux/arm64 --network=none --read-only \
  --pids-limit=64 --cpus=1 --memory=512m \
  --mount type=bind,src="$STUDY_DIR",dst=/study,readonly \
  --mount type=bind,src="$RESULT_DIR",dst=/evidence,readonly \
  python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b \
  python -B /study/audit.py /evidence/raw.json
```

Do not retry either invocation or overwrite `raw.json`. Any nonzero result is
retained as the allocation's terminal outcome; do not run the auditor after a
nonzero formal runner. The command file is preparatory and is not evidence of a
container execution.
