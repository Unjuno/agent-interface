#!/usr/bin/env bash
set -euo pipefail
experiment_dir="${1:?usage: formal_launch.sh EXPERIMENT_DIR FORMAL_OUTPUT PREFLIGHT_OUTPUT}"
formal_output="${2:?missing formal output path}"
preflight_output="${3:?missing preflight output path}"
canonical_output="${experiment_dir}/evidence/formal-04"
canonical_preflight="${experiment_dir}/evidence/preflight-04"
[[ "${formal_output}" == "${canonical_output}" ]] || { echo "STOP: noncanonical formal output" >&2; exit 40; }
[[ "${preflight_output}" == "${canonical_preflight}" ]] || { echo "STOP: noncanonical preflight output" >&2; exit 41; }
[[ ! -L "${experiment_dir}" && ! -L "${experiment_dir}/evidence" && ! -L "${formal_output}" && ! -L "${preflight_output}" ]] || { echo "STOP: symlink output alias" >&2; exit 42; }
canonical_parent="$(cd -P "$(dirname "${experiment_dir}")" && pwd)"
[[ "${canonical_parent}/$(basename "${experiment_dir}")" == "${experiment_dir}" ]] || { echo "STOP: noncanonical experiment directory" >&2; exit 43; }
image_id="sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"
launch_script="${BASH_SOURCE[0]}"
expected_launcher_sha="$(jq -r '.formal_launch_sha256' "${experiment_dir}/FREEZE.json")"
actual_launcher_sha="$(shasum -a 256 "${launch_script}" | awk '{print $1}')"
[[ "${actual_launcher_sha}" == "${expected_launcher_sha}" ]]
[[ "$(docker image inspect "${image_id}" --format '{{.Id}} {{.Os}}/{{.Architecture}}')" == "${image_id} linux/arm64" ]]
mkdir -p "${preflight_output}" "${formal_output}"
[[ -z "$(find "${preflight_output}" -mindepth 1 -print -quit)" && -z "$(find "${formal_output}" -mindepth 1 -print -quit)" ]]
manifest_sha="$(shasum -a 256 "${experiment_dir}/SOURCE_MANIFEST.json" | awk '{print $1}')"
freeze_sha="$(shasum -a 256 "${experiment_dir}/FREEZE.json" | awk '{print $1}')"
prereg_sha="$(shasum -a 256 "${experiment_dir}/PREREGISTRATION.md" | awk '{print $1}')"
source_commit="$(jq -r '.source_commit' "${experiment_dir}/FREEZE.json")"
common_env=(-e "FROZEN_SOURCE_COMMIT=${source_commit}" -e "SOURCE_MANIFEST_SHA256=${manifest_sha}" -e "FREEZE_SHA256=${freeze_sha}" -e "PREREGISTRATION_SHA256=${prereg_sha}")
common_mounts=(-v "${experiment_dir}/src:/src:ro" -v "${experiment_dir}/FREEZE.json:/freeze.json:ro" -v "${experiment_dir}/SOURCE_MANIFEST.json:/source_manifest.json:ro" -v "${experiment_dir}/PREREGISTRATION.md:/preregistration.md:ro")
docker run --rm --platform linux/arm64 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=128m "${common_mounts[@]}" -v "${preflight_output}:/preflight_output:rw" "${common_env[@]}" -e PREFLIGHT_OUTPUT=/preflight_output/preflight.json --entrypoint /usr/bin/python3 "${image_id}" -B /src/validate_freeze.py
docker run --rm --platform linux/arm64 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=128m -v "${experiment_dir}/src:/src:ro" -v "${experiment_dir}/formal_launch.sh:/formal_launch.sh:ro" --workdir /src --entrypoint /usr/bin/python3 "${image_id}" -B -m unittest -v test_unit
docker run --rm --platform linux/arm64 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=128m "${common_mounts[@]}" -v "${preflight_output}:/preflight_output:rw" "${common_env[@]}" -e PREFLIGHT_OUTPUT=/preflight_output/preflight-smoke.json --entrypoint /usr/bin/python3 "${image_id}" -B /src/preflight.py
docker run --rm --platform linux/arm64 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=128m "${common_mounts[@]}" -v "${formal_output}:/evidence:rw" "${common_env[@]}" --entrypoint /usr/bin/python3 "${image_id}" -B /src/runner.py
