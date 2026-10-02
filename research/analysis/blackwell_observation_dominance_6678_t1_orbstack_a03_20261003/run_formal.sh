#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "$0")" && pwd)"
REPO="$(git -C "$PKG" rev-parse --show-toplevel)"
EXPECTED_HEAD="37b973cd28e20b52950f6e5b75668b76f5d4bd65"
BROWSER_IMAGE="mcr.microsoft.com/playwright@sha256:941cc91e5022880ac1d14ae90b476b624deb6399dbbc28d612d5d5bd7928fcbd"
PYTHON_IMAGE="sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e"
OUT="$PKG/formal_01"

test "$(git -C "$REPO" rev-parse HEAD)" = "$EXPECTED_HEAD"
(cd "$PKG" && sha256sum --check SOURCE_SHA256SUMS)
test "$(docker --context orbstack image inspect --format '{{.Id}}' "$BROWSER_IMAGE")" = "sha256:941cc91e5022880ac1d14ae90b476b624deb6399dbbc28d612d5d5bd7928fcbd"
test "$(docker --context orbstack image inspect --format '{{.Id}}' "$PYTHON_IMAGE")" = "$PYTHON_IMAGE"
PLAYWRIGHT_TREE="$(find /Users/taka/node_modules/playwright /Users/taka/node_modules/playwright-core -type f -print0 | LC_ALL=C sort -z | xargs -0 shasum -a 256 | shasum -a 256 | awk '{print $1}')"
EXPECTED_PLAYWRIGHT_TREE="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["images"]["playwright_js_tree_sha256"])' "$PKG/FREEZE.json")"
test "$PLAYWRIGHT_TREE" = "$EXPECTED_PLAYWRIGHT_TREE"
test ! -e "$OUT"
mkdir -p "$OUT/raw" "$OUT/candidate" "$OUT/audit"

capture_name="blackwell-6678-a03-capture-20261003"
docker --context orbstack create --platform linux/arm64 --name "$capture_name" --init --network none --read-only --tmpfs /tmp:rw,nosuid,size=256m --shm-size 128m --cap-drop ALL --security-opt no-new-privileges --cpus 1 --memory 1536m --pids-limit 128 --mount "type=bind,src=$PKG,dst=/src,readonly" --mount "type=bind,src=$OUT/raw,dst=/out" --mount type=bind,src=/Users/taka/node_modules,dst=/opt/pw,readonly -e HOME=/tmp -e NODE_PATH=/opt/pw -e PLAYWRIGHT_MODULE_PATH=/opt/pw/playwright -e PLAYWRIGHT_BROWSERS_PATH=/ms-playwright -e TMPDIR=/tmp -e PLAYWRIGHT_ARTIFACTS_DIR=/tmp/pw-artifacts "$BROWSER_IMAGE" node /src/capture.mjs /out > "$OUT/capture.container-id"
docker --context orbstack inspect "$capture_name" > "$OUT/capture.inspect.pre.json"
set +e
docker --context orbstack start -a "$capture_name" > "$OUT/capture.stdout.log" 2> "$OUT/capture.stderr.log"
capture_rc=$?
set -e
printf '%s\n' "$capture_rc" > "$OUT/capture.exit"
docker --context orbstack inspect "$capture_name" > "$OUT/capture.inspect.post.json"
test "$capture_rc" -eq 0

candidate_name="blackwell-6678-a03-candidate-20261003"
docker --context orbstack create --platform linux/arm64 --name "$candidate_name" --network none --read-only --tmpfs /tmp:rw,nosuid,size=128m --cap-drop ALL --security-opt no-new-privileges --cpus 1 --memory 512m --pids-limit 64 --mount "type=bind,src=$PKG,dst=/src,readonly" --mount "type=bind,src=$OUT/raw,dst=/in,readonly" --mount "type=bind,src=$OUT/candidate,dst=/out" "$PYTHON_IMAGE" python -B /src/candidate.py /in /out/candidate.json > "$OUT/candidate.container-id"
docker --context orbstack inspect "$candidate_name" > "$OUT/candidate.inspect.pre.json"
set +e
docker --context orbstack start -a "$candidate_name" > "$OUT/candidate.stdout.log" 2> "$OUT/candidate.stderr.log"
candidate_rc=$?
set -e
printf '%s\n' "$candidate_rc" > "$OUT/candidate.exit"
docker --context orbstack inspect "$candidate_name" > "$OUT/candidate.inspect.post.json"
test "$candidate_rc" -eq 0

audit_name="blackwell-6678-a03-audit-20261003"
docker --context orbstack create --platform linux/arm64 --name "$audit_name" --network none --read-only --tmpfs /tmp:rw,nosuid,size=128m --cap-drop ALL --security-opt no-new-privileges --cpus 1 --memory 512m --pids-limit 64 --mount "type=bind,src=$PKG,dst=/src,readonly" --mount "type=bind,src=$OUT/raw,dst=/in,readonly" --mount "type=bind,src=$OUT/candidate,dst=/candidate,readonly" --mount "type=bind,src=$OUT/audit,dst=/out" "$PYTHON_IMAGE" python -B /src/auditor.py /in /candidate/candidate.json /out/audit.json > "$OUT/audit.container-id"
docker --context orbstack inspect "$audit_name" > "$OUT/audit.inspect.pre.json"
set +e
docker --context orbstack start -a "$audit_name" > "$OUT/audit.stdout.log" 2> "$OUT/audit.stderr.log"
audit_rc=$?
set -e
printf '%s\n' "$audit_rc" > "$OUT/audit.exit"
docker --context orbstack inspect "$audit_name" > "$OUT/audit.inspect.post.json"
test "$audit_rc" -eq 0

cd "$PKG"
find formal_01 -type f ! -name SHA256SUMS -print | LC_ALL=C sort | while IFS= read -r file; do shasum -a 256 "$file"; done > formal_01/SHA256SUMS
