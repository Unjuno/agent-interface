# OrbStack pilot run record — STOP

- Allocation: `EXTREME-TAIL-ELIGIBILITY-6576-ORB-PILOT-20261002-01`
- Freeze: `FREEZE.json`; source HEAD `53d786ecd5d87f5e7a227f733d1cb51ef0b0d190`.
- Environment: dedicated OrbStack isolated Ubuntu 24.04.5 arm64 machine `agent-interface-6576-pilot-isolated-20261002` (ID `01M3XZS49N838DMW6JACC3B5CD`), 2 vCPU / 4 GiB RAM, Python 3.12.3. Network and file sharing isolation enabled. This was a Linux VM process, **not a Docker container**.
- Frozen input: one stationary-light-tail case, seed 65761001, 4,000 train + 4,000 holdout. Input SHA-256: `395cc683768645794aec04ffa65dc79a59f3c4612dc8c93504b76c2beb721939`.
- Frozen source SHA-256: candidate `d474ed30c29866d3cccf0e8e593bea5135a227878a32636714f40062c54d4107`; auditor `4e37d74b3568e9b1ee88063263a8f2cb186f47eded9d357fc13e326f6e76483a`; gate `006380d64f8c5859e950efb19da8623a89a7b722489619ef2c25411e66b20ff4`; TailID equivalent `1931b354fedb3db2a5cda9c52cdd4c1e9002bb04dbe952980704c282777a63c4`.
- Candidate: invoked once. It completed `run(source)` and failed while writing `pilot/candidate.raw.json`: `PermissionError: [Errno 13] Permission denied`. Read-only diagnosis showed `/home/taka/pilot` was `root:root` mode 755, created by `orbctl push`; no raw output or exit file was persisted. Process exit: 1.
- Auditor: not invoked because the preregistered condition (candidate exit 0) was not met. Retries: 0. No raw rows, audit, or scientific disposition is available.
- Classification: `STOP_INFRA_OUTPUT_DIRECTORY_NOT_WRITABLE`; this is an execution/artifact failure, **not** evidence for or against H. The formal six-case T0 remains unrun and its allocation remains untouched.

## Captured candidate stderr

```text
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/taka/research/analysis/extreme_tail_eligibility_6576_construction_v1/t0_candidate.py", line 230, in <module>
    raise SystemExit(main())
  File "/home/taka/research/analysis/extreme_tail_eligibility_6576_construction_v1/t0_candidate.py", line 225, in main
    output.write_text(json.dumps(run(source), sort_keys=True, separators=(",", ":")) + "\n")
  File "/usr/lib/python3.12/pathlib.py", line 1049, in write_text
    with self.open(mode='w', encoding=encoding, errors=errors, newline=newline) as f:
  File "/usr/lib/python3.12/pathlib.py", line 1015, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
PermissionError: [Errno 13] Permission denied: 'pilot/candidate.raw.json'
```

The same one-shot pilot will not be retried or repaired. Any future run requires a separately preregistered successor allocation. The root-owned destination issue is diagnosed; it does not authorize another invocation under this allocation.
