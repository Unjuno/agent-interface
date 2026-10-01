# Frozen invocation recipe — allocation 09

Use the exact WSL Podman store/runtime recorded in FREEZE.json. Verify the pinned image digest is already local; never pull during the formal run. Confirm correct RTX identity/CDI and exact source hashes. Require stable C: free >=1 GiB, WSL root free >=4 GiB, host RAM free >=8 GiB, and free VRAM >=10 GiB. Inspect Podman containers and NVIDIA process inventory; do not stop or modify anything owned by another task. Unknown owner or failed gate means STOP before CUDA.

Set absolute source and a unique output path. The output path must not exist. One candidate container and bounded host GPU telemetry:

```sh
set -eu
SRC=/ABS/SOURCE
OUT=/ABS/FRESH_OUTPUT
test -d "$SRC"
test ! -e "$OUT"
mkdir -p "$OUT"
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.free --format=csv,noheader > "$OUT/gpu_before.csv"
free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | tr -d ' ')
test "$free_mib" -ge 10240
podman ps --format '{{.ID}},{{.Image}},{{.Status}}' > "$OUT/containers_before.csv"
printf 'timestamp,utilization_gpu_pct,memory_used_mib,memory_free_mib\n' > "$OUT/host_gpu_samples.csv"
nvidia-smi --query-gpu=timestamp,utilization.gpu,memory.used,memory.free --format=csv,noheader,nounits -l 1 >> "$OUT/host_gpu_samples.csv" &
sampler_pid=$!
set +e
podman run --rm --pull=never --network=none --device nvidia.com/gpu=all \
  --cpus=6 --memory=8g --pids-limit=64 --read-only \
  --security-opt=no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$SRC":/src:ro -v "$OUT":/out:rw \
  pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067 \
  python /src/runner.py > "$OUT/candidate.stdout.txt" 2> "$OUT/candidate.stderr.txt"
candidate_exit=$?
kill "$sampler_pid" 2>/dev/null
wait "$sampler_pid" 2>/dev/null
printf '%s\n' "$candidate_exit" > "$OUT/candidate.exit"
set -e
if [ "$candidate_exit" -eq 0 ]; then
  set +e
  podman run --rm --pull=never --network=none --cpus=1 --memory=1g --pids-limit=32 --read-only \
    --security-opt=no-new-privileges -e PYTHONDONTWRITEBYTECODE=1 \
    -v "$SRC":/src:ro -v "$OUT":/out:rw \
    pytorch/pytorch@sha256:831247999fbf7e08f61b3e39f6d77ee434f38f6f07f769d00db451e853878067 \
    python /src/audit.py /out/candidate.jsonl /out/host_gpu_samples.csv /out/audit.json \
    > "$OUT/audit.stdout.txt" 2> "$OUT/audit.stderr.txt"
  audit_exit=$?
  printf '%s\n' "$audit_exit" > "$OUT/audit.exit"
  exit "$audit_exit"
fi
exit "$candidate_exit"
```

The sampler's first row must show at least 10 GiB free and every row must remain above 4 GiB; the independent auditor enforces both. Preserve full argv, stdout, stderr, exit codes, JSON and CSV. Candidate max 1; separate CPU-only auditor max 1 only after candidate exit 0; retries 0.
