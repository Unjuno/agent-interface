# Formal run record — WSLc successor allocation 01

## Candidate (one invocation)

```powershell
wslc.exe run --rm --name ai-wslc-6337-candidate --pull never --network none --cpus 1 --memory 512M `
  --volume "<candidate-src>:/src:ro" --volume "<candidate-out>:/out" `
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f `
  python -B /src/candidate.py /src/fixture.json /out/candidate.raw.json
```

Exit 0; one invocation; outer PowerShell elapsed 2548.89 ms. Candidate raw is 1,093 bytes, SHA-256 `e8c3c30b38f5ab018c0caa272f31f3cdadc960331ba00c1adeb29cf9118f5812`, identical to the predecessor Docker candidate raw. The WSL/cgroup warning is preserved in `candidate.launcher.log`.

## Independent audit (one invocation, only after candidate exit 0)

```powershell
wslc.exe run --rm --name ai-wslc-6337-auditor --pull never --network none --cpus 1 --memory 512M `
  --volume "<auditor-src>:/audit:ro" --volume "<candidate-out>:/candidate:ro" `
  --volume "<auditor-out>:/out" `
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f `
  python -B /audit/auditor.py /audit/fixture.json /candidate/candidate.raw.json /out/audit.raw.json
```

The audit container received no candidate source. Candidate raw was mounted read-only; the audit output used a distinct writable directory. Exit 0; outer PowerShell elapsed 538.4744 ms. Combined launcher output included `PASS_METHOD_SCOPED cases=14 mutations=4/4` and the kernel resource warning. Audit raw SHA-256 is `ec2feb4a3b576f6fa670798168022f2dc9eab0d5a9b069891f24fd976c2fe7d7`.

## Resource and cleanup observations

Both disposable runs used `--rm`, `--pull never`, `--network none`, one requested CPU, and a requested 512 MiB. WSL reported: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` Do not interpret 512 MiB as enforced. The pre-existing exited container `adadf5c4bd8d` (name prefix `ai-wsl301-migration…`) remained untouched. Post-run inventory contained only that same pre-existing row; neither allocation container remained.

The stopwatch is a one-shot process-lifecycle measurement, not a benchmark. Candidate and auditor launcher output was captured as a merged PowerShell stream; it is retained verbatim per command, without claiming separate container stdout/stderr files.
