# Frozen independent audit-only command

One direct Python invocation; no wrapper subprocesses, candidate generation, model, optimizer, CUDA, GPU, network, or WSLc. Only the audit script and frozen input are mounted read-only; output is fresh and writable. Limits are 0.25 CPU, 128 MiB and 32 PIDs.

```sh
docker run --rm --pull=never \
  --name needle-4824-data-audit-successor-20261002-01 \
  --cidfile "$PWD/research/system1/needle_online_correction_4824_wslc_gpu_20261002_01/audit_successor/results/audit-01/container.cid" \
  --network=none --cpus=0.25 --memory=128m --pids-limit=32 --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,size=16m \
  --mount type=bind,src="$PWD/research/system1/needle_online_correction_4824_wslc_gpu_20261002_01/audit_successor/audit_raw.py",dst=/audit/audit_raw.py,readonly \
  --mount type=bind,src="$PWD/research/system1/needle_online_correction_4824_wslc_gpu_20261002_01/audit_successor/FREEZE.json",dst=/audit/FREEZE.json,readonly \
  --mount type=bind,src="$PWD/research/system1/needle_online_correction_4824_wslc_gpu_20261002_01/results/preflight-01/data.json",dst=/input/data.json,readonly \
  --mount type=bind,src="$PWD/research/system1/needle_online_correction_4824_wslc_gpu_20261002_01/audit_successor/results/audit-01",dst=/out \
  --entrypoint python3 \
  sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b \
  -B /audit/audit_raw.py --input /input/data.json --output /out/audit.json --freeze /audit/FREEZE.json
```
