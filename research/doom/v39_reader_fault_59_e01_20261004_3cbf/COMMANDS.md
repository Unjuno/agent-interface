# Frozen execution commands

Native once, then auditor once only after native exit0. No replay.

```bash
/usr/local/bin/orbctl run -m research-6183-t0-20261003 -u root docker run --network none --cpus 1 --memory 512m --memory-swap 512m --pids-limit 64 --read-only --cap-drop ALL --security-opt no-new-privileges --user 501:501 --tmpfs /tmp:rw,nosuid,size=64m --mount type=bind,source=/home/taka/inputs/v39-reader-e01-3cbf,target=/source,readonly --workdir /source --env PYTHONDONTWRITEBYTECODE=1 --name v39-reader-e01-3cbf-native --mount type=bind,source=/home/taka/outputs/v39-reader-e01-3cbf-native,target=/out sha256:c4839671ed0625dd38a53d8ed542bab16407c2b4c88a5ac84431695438c2b816 python3 -B probe.py /out/record
/usr/local/bin/orbctl run -m research-6183-t0-20261003 -u root docker run --network none --cpus 1 --memory 512m --memory-swap 512m --pids-limit 64 --read-only --cap-drop ALL --security-opt no-new-privileges --user 501:501 --tmpfs /tmp:rw,nosuid,size=64m --mount type=bind,source=/home/taka/inputs/v39-reader-e01-3cbf,target=/source,readonly --workdir /source --env PYTHONDONTWRITEBYTECODE=1 --name v39-reader-e01-3cbf-audit --mount type=bind,source=/home/taka/outputs/v39-reader-e01-3cbf-native,target=/native,readonly --mount type=bind,source=/home/taka/outputs/v39-reader-e01-3cbf-audit,target=/out sha256:c4839671ed0625dd38a53d8ed542bab16407c2b4c88a5ac84431695438c2b816 python3 -B audit.py /native/record /out/record
```

Peer sidecar writes/first native results are retained exactly. Names and output
paths must not exist with earlier contents; source SHA256 checked by extractor.
Container inspect before/after and immutable image identity retained separately.
