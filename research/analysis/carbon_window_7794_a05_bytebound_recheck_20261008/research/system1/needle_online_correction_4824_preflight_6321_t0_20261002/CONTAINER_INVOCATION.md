# Frozen OrbStack CPU preflight command

Image was already present locally and matched immutable ID `sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b` (`linux/arm64`). No network, image pull, CUDA/GPU, model, or optimizer update. Root and source mounts are read-only; only the fresh output directory is writable. Limits: 0.25 CPU, 128 MiB RAM, 32 PIDs.

```sh
docker run --rm --pull=never \
  --name needle-4824-label-preflight-20261002-01 \
  --network=none --cpus=0.25 --memory=128m --pids-limit=32 --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=16m \
  --mount type=bind,src="$PWD/research/system1/needle_online_correction_4824_wslc_gpu_20261002_01",dst=/exp,readonly \
  --mount type=bind,src="$PWD/research/system1/needle_online_correction_4824_wslc_gpu_20261002_01/results/preflight-01",dst=/out \
  --entrypoint python3 \
  sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b \
  -B /exp/run_preflight.py --package /exp --output /out
```
