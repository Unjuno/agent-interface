# Formal A01 commands and container receipts

The command bodies below ran once each inside the dedicated OrbStack VM. The `orb -m research-6680-a01-20261003 -u root` prefix was used from macOS to address its private Docker Engine.

Candidate:

```sh
docker run --name 6680-a01-candidate --network none --cpus 0.25 --memory 256m --memory-swap 256m --pids-limit 32 --read-only --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --env PYTHONDONTWRITEBYTECODE=1 --mount type=bind,src=/home/taka/6680-a01/src,dst=/src,readonly --mount type=bind,src=/home/taka/6680-a01/out-candidate,dst=/out --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/temporal_candidate.py /out/candidate.raw.json
```

Auditor (started only after candidate exit 0):

```sh
docker run --name 6680-a01-auditor --network none --cpus 0.25 --memory 256m --memory-swap 256m --pids-limit 32 --read-only --cap-drop ALL --security-opt no-new-privileges --user 1000:1000 --env PYTHONDONTWRITEBYTECODE=1 --mount type=bind,src=/home/taka/6680-a01/src,dst=/src,readonly --mount type=bind,src=/home/taka/6680-a01/out-candidate,dst=/candidate,readonly --mount type=bind,src=/home/taka/6680-a01/out-audit,dst=/out --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python /src/temporal_auditor.py /candidate/candidate.raw.json /out/audit.json
```

The candidate output directory was newly created on the clean, newly provisioned VM. The audit output directory was explicitly checked empty before auditor launch. Docker inspect receipts preserve configured resource limits, read-only mounts/root, `network=none`, exit status, OOM state, and container IDs.
