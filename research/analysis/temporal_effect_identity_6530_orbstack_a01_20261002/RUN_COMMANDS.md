# Allocation A01 command and launch receipts

All commands below were executed in OrbStack VM `agent-interface-6576-tailid-parity-a03-20261002` against its private Docker Engine. Source directories were prepared read-only; output directories were separate. Candidate and auditor containers were created and their configs inspected before either was started.

## Candidate container (created once, started once)

```sh
docker create --name 6530-temporal-a01-candidate --network none --read-only --cpus=1 --memory=2g --memory-swap=2g \
  --mount type=bind,source=/home/taka/6530a01/candidate-src,target=/src,readonly \
  --mount type=bind,source=/home/taka/6530a01/results/candidate,target=/out \
  --entrypoint python python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 \
  -B /src/candidate.py /src/fixture.json /out/candidate.json

docker start -a 6530-temporal-a01-candidate
```

Start exit: 0; inspected container exit: 0; candidate raw is `formal_01/candidate/candidate.json`.

## Independent raw-only auditor container (created once, started once)

```sh
docker create --name 6530-temporal-a01-auditor --network none --read-only --cpus=1 --memory=2g --memory-swap=2g \
  --mount type=bind,source=/home/taka/6530a01/audit-src,target=/src,readonly \
  --mount type=bind,source=/home/taka/6530a01/results/candidate,target=/raw,readonly \
  --mount type=bind,source=/home/taka/6530a01/results/audit,target=/out \
  --entrypoint python python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016 \
  -B /src/audit.py /raw/candidate.json /src/truth.json /out/audit.json

docker start -a 6530-temporal-a01-auditor
```

Start exit: 0; inspected container exit: 0; audit says `PASS`, 8 rows, no errors.

## Preserved setup command error

Before the successful auditor container was created, one `docker create` command was rejected with `invalid checksum digest length`. The malformed image argument was `python:3.12-slim@sha256:dddfd7e07f9d15aeeca615057d53c0d6cfe30f62`; Docker created no container. This occurred before either scientific process started. The image digest was checked against `FREEZE.json`, then the corrected command above was used. It is recorded as a command-entry/setup error; there was no candidate or auditor process retry.

## Exact inspection fields

Before start both container IDs were inspected. Both reported the frozen image reference, `network=none`, `readonly=true`, `cpus=1000000000`, `mem=2147483648`, `swap=2147483648`, and separate RO/RW bind mounts as specified above. Candidate ID: `905f490a11a5e050786adc047910a89a47134165c12b3d7450bd4ba56a0867fa`. Auditor ID: `d7e30f1c2b530fd181b78d56e9332f319820be1e2a127242143364e00b4c3b8c`.
