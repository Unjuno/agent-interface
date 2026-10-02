# Frozen OrbStack A03 invocation template

Machine: `research-6680-a01-20261003` (separate Docker Engine 29.1.3). VM paths are under `/home/taka/6616-a03-20261003/`. The candidate container is run once. Only on candidate exit 0 may the separate auditor container run once. Both container records and exact host stdout/stderr are retained; neither container is removed before inspection.

The host computes `FREEZE_SHA256` as the SHA-256 of the exact committed `FREEZE.json`, verifies the VM image ID/platform and that the allocation-specific source/output paths do not exist, pushes only frozen source inputs, creates two fresh empty output directories, then runs:

```sh
docker run --name 6616-a03-candidate-20261003 --network none --cpus 0.25 --memory 256m --memory-swap 256m --pids-limit 32 --read-only --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --mount type=bind,src=/home/taka/6616-a03-20261003/src,dst=/src,readonly --mount type=bind,src=/home/taka/6616-a03-20261003/src/FREEZE.json,dst=/freeze/FREEZE.json,readonly --mount type=bind,src=/home/taka/6616-a03-20261003/out-candidate,dst=/out --workdir /tmp -e OBSTAC_ALLOCATION_ID=history-conditioned-reliance-6616-t0-a03-20261003 -e OBSTAC_SOURCE_COMMIT=c17490cae4cb1e9600b816484f5103e3613700af -e OBSTAC_IMAGE_ID=sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f -e OBSTAC_FREEZE_SHA256=$FREEZE_SHA256 -e OBSTAC_CONSTRUCTION=0 python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /src/candidate.py /src/fixture.json /freeze/FREEZE.json /out/run
```

Record and inspect candidate exit/OOM/container/mounts and retain both output files. If candidate exits nonzero or either output is absent/invalid, stop permanently before the auditor.

On candidate exit 0, with the candidate output mounted read-only and a distinct new auditor output directory:

```sh
docker run --name 6616-a03-auditor-20261003 --network none --cpus 0.25 --memory 256m --memory-swap 256m --pids-limit 32 --read-only --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --mount type=bind,src=/home/taka/6616-a03-20261003/src,dst=/src,readonly --mount type=bind,src=/home/taka/6616-a03-20261003/src/FREEZE.json,dst=/freeze/FREEZE.json,readonly --mount type=bind,src=/home/taka/6616-a03-20261003/out-candidate,dst=/candidate,readonly --mount type=bind,src=/home/taka/6616-a03-20261003/out-audit,dst=/out --workdir /tmp -e OBSTAC_ALLOCATION_ID=history-conditioned-reliance-6616-t0-a03-20261003 -e OBSTAC_SOURCE_COMMIT=c17490cae4cb1e9600b816484f5103e3613700af -e OBSTAC_IMAGE_ID=sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f -e OBSTAC_FREEZE_SHA256=$FREEZE_SHA256 -e OBSTAC_CONSTRUCTION=0 python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /src/audit.py /src/fixture.json /src/oracle.json /freeze/FREEZE.json /candidate/run/candidate.raw.json /candidate/run/reviewer_packets.json /out/run/audit.json
```

These are argument templates; the actual invocation receipt records the expanded freeze digest and exact argv. Any failure is a terminal STOP with no retry.
