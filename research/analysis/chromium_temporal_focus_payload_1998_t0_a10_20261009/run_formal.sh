#!/bin/bash
set -u
set -o pipefail

PKG="research/analysis/chromium_temporal_focus_payload_1998_t0_a10_20261009"
RESULTS="$PKG/results"
FRAME_DIR="research/observation_gating/results/baseline-screen-02/chromium-1101-O0/frames"
IMAGE="node@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80"

if [[ -e "$RESULTS" ]]; then
  echo "STOP: formal results path already exists" >&2
  exit 73
fi
mkdir -p "$RESULTS/artifacts"

docker run --rm --pull=never --network none --read-only \
  --cap-drop=ALL --security-opt=no-new-privileges --pids-limit=32 \
  --cpus=1 --memory=256m --user 1000:1000 \
  --tmpfs /tmp:rw,nosuid,nodev,noexec,size=16m \
  --mount "type=bind,src=/tmp/agent-interface-1998-pillow-a04/$PKG,dst=/src,readonly" \
  --mount "type=bind,src=/tmp/agent-interface-1998-pillow-a04/$FRAME_DIR,dst=/inputs,readonly" \
  --mount "type=bind,src=/tmp/agent-interface-1998-pillow-a04/$RESULTS,dst=/results" \
  "$IMAGE" node /src/src/candidate.js \
  >"$RESULTS/candidate.stdout" 2>"$RESULTS/candidate.stderr"
candidate_exit=$?
printf '%s\n' "$candidate_exit" > "$RESULTS/candidate.exit"

auditor_exit=125
if [[ "$candidate_exit" -eq 0 ]]; then
  sandbox-exec -p '(version 1) (allow default) (deny network*)' \
    python3 "$PKG/auditor.py" --package "$PKG" \
    >"$RESULTS/auditor.stdout" 2>"$RESULTS/auditor.stderr"
  auditor_exit=$?
else
  : > "$RESULTS/auditor.stdout"
  printf '%s\n' 'auditor not run because candidate exit was nonzero' > "$RESULTS/auditor.stderr"
fi
printf '%s\n' "$auditor_exit" > "$RESULTS/auditor.exit"

python3 - "$RESULTS" "$candidate_exit" "$auditor_exit" "$IMAGE" <<'PY'
import json, pathlib, sys, time
root=pathlib.Path(sys.argv[1])
record={"allocation":"LABEL-CONTROL-AMBIGUITY-1998-T0-A10-20261009",
        "candidate_invocations":1,"candidate_exit":int(sys.argv[2]),
        "auditor_invocations":1 if int(sys.argv[2])==0 else 0,
        "auditor_exit":int(sys.argv[3]),"container_image":sys.argv[4],
        "network":"none","rootfs":"read-only","cpus":1,"memory_bytes":268435456,
        "pids_limit":32,"result_recorded_time_utc":time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        "retries":0}
(root/'RUN.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
PY

if [[ "$candidate_exit" -ne 0 || "$auditor_exit" -ne 0 ]]; then
  exit 1
fi
