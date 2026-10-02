#!/usr/bin/env bash
set -euo pipefail

wslc="/mnt/c/Program Files/WSL/wslc.exe"
image='python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'
probe_path="$(mktemp -d "${TMPDIR:-/tmp}/agent-interface-wslc-probe.XXXXXXXX")"
container_name="agent-interface-wslc-probe-$(cat /proc/sys/kernel/random/uuid | tr -d '-')"
cleanup() {
  rm -f -- "$probe_path/sentinel.bin"
  rmdir -- "$probe_path"
}
trap cleanup EXIT
printf 'wslc-readonly-probe' > "$probe_path/sentinel.bin"
probe_code="import errno; from pathlib import Path; p=Path('/probe/sentinel.bin'); assert p.read_bytes()==b'wslc-readonly-probe'; exec(\"try:\\n p.write_bytes(b'blocked')\\nexcept OSError as e:\\n assert e.errno==errno.EROFS\\n print('read-only bind mount: PASS (EROFS)')\\nelse:\\n raise SystemExit('write unexpectedly allowed')\")"

"$wslc" run --rm --name "$container_name" --pull never --network none --memory 512M --cpus 1 \
  --volume "$probe_path:/probe:ro" "$image" python -B -c "$probe_code"
containers="$("$wslc" container list --all)"
if grep -Fq "$container_name" <<<"$containers"; then
  printf 'container remained after --rm: %s\n' "$container_name" >&2
  exit 1
fi
printf 'WSLc Linux-filesystem probe: PASS; network=none; memory=512M; cpus=1; cleanup=verified\n'
printf 'Kernel warning: swap/cgroup memory isolation unavailable; peak-memory enforcement is untested.\n'

