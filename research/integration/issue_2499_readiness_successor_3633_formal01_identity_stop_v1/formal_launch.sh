#!/usr/bin/env bash
set -euo pipefail
experiment_dir="${1:?usage: formal_launch.sh EXPERIMENT_DIR FORMAL_OUTPUT PREFLIGHT_OUTPUT AUDIT_OUTPUT}"
formal_output="${2:?missing formal output path}"
preflight_output="${3:?missing preflight output path}"
audit_output="${4:?missing audit output path}"
image_id="sha256:f8ae93cfedd412cfe39ca575a97abc32c4d6e99ee7b5cc7848e79e0ce08bdc9f"
expected_launcher_sha="$(jq -r '.formal_launch_sha256' "${experiment_dir}/FREEZE.json")"
actual_launcher_sha="$(shasum -a 256 "${BASH_SOURCE[0]}" | awk '{print $1}')"
[[ "${actual_launcher_sha}" == "${expected_launcher_sha}" ]]
[[ "$(docker image inspect "${image_id}" --format '{{.Id}} {{.Os}}/{{.Architecture}}')" == "${image_id} linux/arm64" ]]
for dir in "${formal_output}" "${preflight_output}" "${audit_output}"; do
  if [[ -e "${dir}" ]]; then [[ -d "${dir}" && -z "$(find "${dir}" -mindepth 1 -print -quit)" ]]; else mkdir -p "${dir}"; fi
done
manifest_sha="$(shasum -a 256 "${experiment_dir}/SOURCE_MANIFEST.json" | awk '{print $1}')"
freeze_sha="$(shasum -a 256 "${experiment_dir}/FREEZE.json" | awk '{print $1}')"
prereg_sha="$(shasum -a 256 "${experiment_dir}/PREREGISTRATION.md" | awk '{print $1}')"
source_commit="$(jq -r '.source_commit' "${experiment_dir}/FREEZE.json")"
common=(--rm --platform linux/arm64 --network none --read-only --tmpfs /tmp:rw,nosuid,size=512m
  -v "${experiment_dir}/src:/src:ro" -v "${experiment_dir}/FREEZE.json:/freeze.json:ro"
  -v "${experiment_dir}/SOURCE_MANIFEST.json:/source_manifest.json:ro"
  -v "${experiment_dir}/PREREGISTRATION.md:/preregistration.md:ro"
  -e "FROZEN_SOURCE_COMMIT=${source_commit}" -e "SOURCE_MANIFEST_SHA256=${manifest_sha}"
  -e "FREEZE_SHA256=${freeze_sha}" -e "PREREGISTRATION_SHA256=${prereg_sha}" -e "PINNED_IMAGE_ID=${image_id}")
docker run "${common[@]}" --entrypoint /usr/bin/python3 "${image_id}" -B /src/validate_freeze.py
docker run "${common[@]}" --workdir /src --entrypoint /usr/bin/python3 "${image_id}" -B -m unittest -v test_readiness
docker run "${common[@]}" -v "${preflight_output}:/preflight:rw" -e PREFLIGHT_OUTPUT=/preflight/receipt.json \
  --entrypoint /usr/bin/python3 "${image_id}" -B /src/preflight.py
[[ -z "$(find "${formal_output}" -mindepth 1 -print -quit)" ]]
docker run "${common[@]}" -v "${formal_output}:/evidence:rw" -e EVIDENCE_PATH=/evidence/result.json \
  --entrypoint /usr/bin/python3 "${image_id}" -B /src/formal_session.py
docker run "${common[@]}" -v "${formal_output}:/input:ro" -v "${audit_output}:/audit:rw" -e AUDIT_OUTPUT=/audit/audit.json \
  --entrypoint /usr/bin/python3 "${image_id}" -B /src/audit_session.py
