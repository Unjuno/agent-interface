# Frozen invocation recipe — do not run until gates pass

From WSL Arch, verify exact local image digest without pulling:
`podman image inspect pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067`

Check GPU identity and current global use with `nvidia-smi`; verify CDI using the already-configured Podman runtime. Record free VRAM >=10 GiB, current processes/containers and stable disk/RAM readings. Confirm the output directory does not exist and the mounted source matches FREEZE.json and SHA256SUMS. If any check fails or another process owner is unknown, do not launch.

One candidate invocation only (replace the three absolute host paths after confirming them):
```sh
podman run --rm --pull=never --network=none --device nvidia.com/gpu=all \
  --cpus=6 --memory=8g --pids-limit=64 --read-only \
  --security-opt=no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v /ABS/SOURCE:/src:ro -v /ABS/FRESH_OUTPUT:/out:rw \
  pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067 \
  python /src/runner.py
```

Save the complete argv/stdout/stderr/exit sidecars. Capture `nvidia-smi --query-gpu=timestamp,utilization.gpu,memory.used,memory.free --format=csv -l 1` for the bounded candidate interval and stop the sampler immediately after the single candidate exits. Verify global free VRAM never falls below 4 GiB. Run `python /src/audit.py /ABS/FRESH_OUTPUT/candidate.jsonl /ABS/FRESH_OUTPUT/audit.json` once, CPU-only and raw-only, only if candidate exit is 0. Never retry.
