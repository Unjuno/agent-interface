# A05 execution record

Frozen allocation: `CONFUSION-ADAPTIVE-PRACTICE-8084-A05-20261005-01`; base main `10be950b8fb6e2799b837b541577fb5f32db858d`; see [FREEZE.json](FREEZE.json) for source/input hashes and image identity.

Construction checks in WSLc: `python -m unittest -v test_method` and `python -O -m unittest -v test_method`; both 3/3 passed. Fixture generator exited 0 and emitted 12,000 rows. Candidate invoked exactly once (exit 0; 12,000 rows); auditor invoked exactly once (exit 0; `METHOD_PASS_SCOPED`, zero base errors, five mutations rejected). The auditor's separate output contains the full stratified summary.

WSLc image: `agent-interface/native-suite-wslc-a08:20261004`, `sha256:1b4a8bd7c0fe372cc0cafa74af433b8ae1f73f1bee0f11a028f126b08b2c128a`; Python 3.12.14; `--network none`; read-only candidate and auditor mounts; 1 CPU and 512 MiB requested. Both mount preflights exposed only their allowlisted files. The host emitted `Your kernel does not support swap limit capabilities or the cgroup is not mounted`; hard memory/swap enforcement is therefore unverified.

Reproduction (from this allocation directory in PowerShell; each `wslc run` creates a disposable container):

```powershell
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --volume "${PWD}:/work:ro" --workdir /work --entrypoint python agent-interface/native-suite-wslc-a08:20261004 -m unittest -v test_method
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --volume "${PWD}:/work:ro" --workdir /work --entrypoint python agent-interface/native-suite-wslc-a08:20261004 -O -m unittest -v test_method
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --volume "${PWD}:/work:rw" --workdir /work --entrypoint python agent-interface/native-suite-wslc-a08:20261004 /work/generate.py
```

Formal candidate (from the `candidate/` directory; run output/stderr redirected to the package's `results/`):

```powershell
$pkg = (Resolve-Path ..).Path
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --volume "${PWD}:/work:ro" --workdir /work --entrypoint python agent-interface/native-suite-wslc-a08:20261004 /work/candidate.py 1> (Join-Path $pkg 'results/candidate.stdout.json') 2> (Join-Path $pkg 'results/candidate.stderr.txt')
```

The candidate stdout was copied byte-for-byte to `auditor/candidate.raw.json` (SHA-256 `80FC11F7067F45F09549C891ABAD0B409B6D1A01E632ECBD941B0105718483CA`), with the exact source/destination paths checked before launch. Formal auditor (from package root):

```powershell
$auditDir = (Resolve-Path auditor).Path
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --volume "${auditDir}:/work:ro" --workdir /work --entrypoint python agent-interface/native-suite-wslc-a08:20261004 /work/auditor.py 1> results/auditor.stdout.json 2> results/auditor.stderr.txt
```

Captured stdout/stderr and raw candidate output are in `results/`.
