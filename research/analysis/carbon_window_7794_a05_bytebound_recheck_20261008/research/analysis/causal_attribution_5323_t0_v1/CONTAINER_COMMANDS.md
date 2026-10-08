# Frozen container commands

Allocation: `causal-attribution-5323-t0-20260930-01`.

Run once from the repo root. Source is mounted read-only, the root filesystem is
read-only, networking is disabled, and only the unique result directory is
writable. The auditor is a separate container and runs only after runner exit
0. Never overwrite output or retry.

```sh
docker run --rm --pull=never --platform linux/arm64 --network=none --read-only \
  --pids-limit=32 --cpus=1 --memory=256m \
  --mount type=bind,src="$STUDY_DIR",dst=/study,readonly \
  --mount type=bind,src="$RESULT_DIR",dst=/out \
  python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b \
  python -B /study/run.py /out/raw.json
```

```sh
docker run --rm --pull=never --platform linux/arm64 --network=none --read-only \
  --pids-limit=32 --cpus=1 --memory=256m \
  --mount type=bind,src="$STUDY_DIR",dst=/study,readonly \
  --mount type=bind,src="$RESULT_DIR",dst=/evidence,readonly \
  python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b \
  python -B /study/audit.py /evidence/raw.json
```
