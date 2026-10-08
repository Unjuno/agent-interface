# E04 one-shot execution

PRELAUNCH until independent review clears the frozen inputs. Each formal
container at most once; no --rm, replacement, retry or resume on failure.
All host commands use /bin/bash. The E03 source below is immutable read-only
input, not reuse of E03 output or allocation.

Fresh guest root: /home/taka/e04-native-fault-formal-3cbf-20261004.
Experiment package copied into its experiment/ directory; native output out/
initially empty. Bind source is the existing verified 1917-file closure at
/home/taka/e03-native-fault-formal-3cbf-20261004/source/unjuno-e03-frozen.smfv75.

```
/usr/local/bin/orbctl run -m research-6183-t0-20261003 -u root docker run \
 --name e04-native-fault-formal-3cbf-20261004 --network none --cpus 1 \
 --memory 1g --memory-swap 1g --pids-limit 128 --read-only --cap-drop ALL \
 --security-opt no-new-privileges --user 501:501 --tmpfs /tmp:rw,nosuid,size=256m \
 --mount type=bind,source=/home/taka/e03-native-fault-formal-3cbf-20261004/source/unjuno-e03-frozen.smfv75,target=/source,readonly \
 --mount type=bind,source=/home/taka/e04-native-fault-formal-3cbf-20261004/experiment,target=/experiment,readonly \
 --mount type=bind,source=/home/taka/e04-native-fault-formal-3cbf-20261004/out,target=/out \
 --workdir /out --env PYTHONPATH=/source --env PYTHONDONTWRITEBYTECODE=1 \
 sha256:560af28c711a2bf94cf9bedef4f5e47b26f86ea5bc79211c603addb74237540b \
 timeout 60s python3 -B /experiment/runner.py --source /source --out /out/record
```

After terminal, retain full docker inspect and docker logs. Use docker cp to
export /out/record/. into a distinct fresh export/ directory. Do not modify
either record. The offline audit requires exact file-set and byte-hash equality.
Distinct auditor e04-native-fault-auditor-3cbf-20261004: network none,
CPU1/memory512MiB/swap0/pids64, UID501, read-only root and read-only binds
experiment -> /experiment, out -> /native, export -> /export,
native-container-inspect.json -> /receipt.json, fresh audit -> /audit;
cap-drop ALL/no-new-privileges/tmpfs64MiB. Exact auditor command:

```
python3 -B /experiment/audit.py --root /experiment --record /native/record \
 --export /export --native-inspect /receipt.json --out /audit/AUDIT.json
```

Save auditor terminal/logs even if no AUDIT.json is produced. An audit failure
never authorizes replay of either formal container. Tests use retained E03
records read-only for construction compatibility, never execute old auditors.
