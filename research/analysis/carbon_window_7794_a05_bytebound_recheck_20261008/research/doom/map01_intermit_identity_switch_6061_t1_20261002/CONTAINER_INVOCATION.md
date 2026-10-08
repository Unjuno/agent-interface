# One-shot OrbStack invocation

The run used the already-present immutable image ID; it did not pull or rebuild an image. Source/input were mounted read-only, the root filesystem was read-only, networking was disabled, and only the output directory was writable. Limits: 0.25 CPU, 128 MiB, 32 PIDs, and 16 MiB tmpfs. Candidate and independent auditor ran once each; no retry.

```sh
docker run --rm --pull=never \
  --name identity-switch-6061-t1-20261002-01 \
  --cidfile research/doom/map01_intermit_identity_switch_6061_t1_20261002/results/allocation-01/container.cid \
  --network=none --cpus=0.25 --memory=128m --pids-limit=32 --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=16m \
  --mount type=bind,src="$PWD/research/doom/map01_intermit_identity_switch_6061_t1_20261002",dst=/exp,readonly \
  --mount type=bind,src="$PWD/research/doom/map01_intermit_identity_switch_6061_t1_20261002/results/allocation-01",dst=/out \
  --entrypoint python3 \
  sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b \
  -B /exp/run_formal.py \
  --input /exp/input.json --truth /exp/truth.json \
  --candidate /exp/candidate.py --audit /exp/audit.py \
  --freeze /exp/FREEZE.json --out /out
```

The historical container hostname and full container ID are retained in `results/allocation-01/RUN.json` and `container.cid`. Docker `--rm` removed the disposable container at exit. Pre-existing resources were inventoried read-only and left untouched; no exclusive shared-slot claim was obtained. Outcome: `PASS_METHOD_SCOPED_WITH_IDENTIFIABILITY_HOLD` / `HOLD_SILENT_IDENTITY_SWITCH_UNOBSERVABLE`, not a live allocation.
