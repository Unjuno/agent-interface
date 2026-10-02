# T7 commands and process captures

Host-only construction before freeze (not candidate/auditor allocation):

```powershell
python -B -m unittest -v test_protocol
python -B -m py_compile candidate.py audit.py test_protocol.py
```

The two unit tests passed before measurement. The formal candidate was then run once, with the read-only source bind and raw stdout capture:

```powershell
$src = (Resolve-Path .).Path
$mount = "type=bind,source=$src,target=/src,readonly"
wslc run --name sr5442-t7-candidate-01 --pull never --network none --cpus 1 --memory 1G --user 65534:65534 --mount $mount --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B candidate.py > formal_01/candidate.raw.json
```

Observed exit 0; stdout is `formal_01/candidate.raw.json`. Stderr: `wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.`

After verifying that the raw parses as one JSON object with exactly four rows, the independent auditor was run once in a separate container with both mounts read-only:

```powershell
$src = (Resolve-Path .).Path
$raw = (Resolve-Path formal_01/candidate.raw.json).Path
$sourceMount = "type=bind,source=$src,target=/src,readonly"
$rawMount = "type=bind,source=$raw,target=/in/raw.json,readonly"
wslc run --name sr5442-t7-auditor-01 --pull never --network none --cpus 1 --memory 1G --user 65534:65534 --mount $sourceMount --mount $rawMount --workdir /src python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B audit.py /in/raw.json > formal_01/audit.json
```

Observed exit 0; stdout is `formal_01/audit.json`. The same swap/cgroup warning was emitted to stderr. Formal invocations=2 total (one candidate, one auditor), retries=0. No further candidate or auditor invocation occurred.
