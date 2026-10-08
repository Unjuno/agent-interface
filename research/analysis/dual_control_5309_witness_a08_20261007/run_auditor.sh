#!/bin/sh
set -eu
alloc_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mode=${1:-formal}
case "$mode" in
  smoke) raw_source=${alloc_root}/candidate-input.json; set -- python -I -S -B -c 'import os; assert os.path.isfile("/code/auditor.py"); assert os.path.isfile("/input/oracle.json"); assert os.path.isfile("/input/candidate-input.json"); assert os.path.isfile("/input/candidate-raw.json"); assert not os.path.exists("/input/candidate.py"); print("AUDITOR_MOUNT_ISOLATION_OK")' ;;
  formal) raw_source=${alloc_root}/out/candidate-raw.json; set -- python -I -S -B /code/auditor.py ;;
  *) printf '%s\n' 'usage: run_auditor.sh [smoke]' >&2; exit 2 ;;
esac
exec docker run --rm --platform linux/arm64 --name ai5309-witness-a08-auditor-20261007 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cap-drop ALL --security-opt no-new-privileges --pids-limit 32 --memory 256m --cpus 1 --user 501:20 --mount "type=bind,src=${alloc_root}/auditor.py,dst=/code/auditor.py,readonly" --mount "type=bind,src=${alloc_root}/candidate-input.json,dst=/input/candidate-input.json,readonly" --mount "type=bind,src=${alloc_root}/oracle.json,dst=/input/oracle.json,readonly" --mount "type=bind,src=${raw_source},dst=/input/candidate-raw.json,readonly" --mount "type=bind,src=${alloc_root}/out,dst=/out" --workdir /work python@sha256:c845af9399020c7e562969a13689e929074a10fd057acd1b1fad06a2fb068e97 "$@"
