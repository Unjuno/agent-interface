#!/bin/sh
# One-shot entrypoint. No pulls, installs, network, retries or GPU access.
set -eu
IMAGE="${IMAGE:-agent-interface-gtk-preflight:local}"
EXPECTED="sha256:e2a7634d2b9627ec037c488d6aa472c6c00d5ef0dda6e302f7dced8b9b8752d4"
ACTUAL="$(docker image inspect "$IMAGE" --format '{{.Id}}')"
[ "$ACTUAL" = "$EXPECTED" ] || { echo "STOP_IMAGE_ID_MISMATCH expected=$EXPECTED actual=$ACTUAL" >&2; exit 20; }
docker run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  --security-opt no-new-privileges --cap-drop ALL \
  -v "$PWD:/src:ro" -v "$PWD/results:/results:rw" \
  --entrypoint /bin/sh "$IMAGE" -ec '
    cd /src
    python3 -m unittest -v test_temporal_protocol.py
    python3 run_formal.py --out /results/formal01
  '
