#!/usr/bin/env bash
set -euo pipefail

package="research/analysis/counterexample_guard_coverage_gate_6645_t1_v1"
image="python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f"
formal="$package/results/formal_01"
mkdir -p "$formal/candidate" "$formal/auditor"

create_and_run() {
  local role="$1"
  local name="cggate-6645-t1-${role}-orb-20261003"
  local command_path="$2"
  local output_path="$3"
  local result_dir="$formal/$role"
  local container_id

  shift 3
  docker create --pull=never --name "$name" --network none \
    --cpus=1 --memory=536870912 --memory-swap=1073741824 --pids-limit=64 \
    --read-only --cap-drop=ALL --security-opt=no-new-privileges \
    --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 \
    --mount "type=bind,source=$(pwd)/$package,target=/work,readonly" \
    "$image" python "$command_path" "$@" > "$result_dir/container_id.txt"
  container_id="$(<"$result_dir/container_id.txt")"
  docker inspect "$container_id" > "$result_dir/container_inspect_pre.json"
  set +e
  docker start -a "$container_id" > "$output_path" 2> "$result_dir/stderr.log"
  local exit_code=$?
  set -e
  printf '%s\n' "$exit_code" > "$result_dir/exit_code.txt"
  docker inspect "$container_id" > "$result_dir/container_inspect_post.json"
  if [[ "$exit_code" -ne 0 ]]; then
    return "$exit_code"
  fi
}

create_and_run candidate /work/candidate.py \
  "$formal/candidate/raw.json" /work/fixture.json /work/contract.json
create_and_run auditor /work/auditor.py \
  "$formal/auditor/audit.json" /work/fixture.json /work/contract.json \
  /work/results/formal_01/candidate/raw.json
