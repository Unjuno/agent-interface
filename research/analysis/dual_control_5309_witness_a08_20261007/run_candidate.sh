#!/bin/sh
set -eu
alloc_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mode=${1:-formal}
case "$mode" in
  smoke) set -- python -I -S -B -c 'import os; assert os.path.isfile("/code/candidate.py"); assert os.path.isfile("/input/candidate-input.json"); assert not os.path.exists("/input/oracle.json"); assert not os.access("/code/candidate.py", os.W_OK); print("CANDIDATE_MOUNT_ISOLATION_OK")' ;;
  formal) set -- python -I -S -B /code/candidate.py ;;
  *) printf '%s\n' 'usage: run_candidate.sh [smoke]' >&2; exit 2 ;;
esac
exec docker run --rm --platform linux/arm64 --name ai5309-witness-a08-candidate-20261007 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cap-drop ALL --security-opt no-new-privileges --pids-limit 32 --memory 256m --cpus 1 --user 501:20 --mount "type=bind,src=${alloc_root}/candidate.py,dst=/code/candidate.py,readonly" --mount "type=bind,src=${alloc_root}/candidate-input.json,dst=/input/candidate-input.json,readonly" --mount "type=bind,src=${alloc_root}/out,dst=/out" --workdir /work python@sha256:c845af9399020c7e562969a13689e929074a10fd057acd1b1fad06a2fb068e97 "$@"
