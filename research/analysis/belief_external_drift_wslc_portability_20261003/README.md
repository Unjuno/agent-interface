# WSLc portability replay — external-transition belief T0

Status: preregistered runtime-portability replay only. This does not revise or replace the original Windows-host result at [`belief_external_drift_5368_t0_20261003/`](../belief_external_drift_5368_t0_20261003/).

- Parent Issue: [#5368 — Action-conditioned belief contracts](https://github.com/Unjuno/agent-interface/issues/5368)
- Existing result: `PASS_METHOD_SCOPED`, nine finite synthetic traces, source frozen and merged at PR #6972.
- New allocation: `belief-external-drift-5368-wslc-portability-20261003-a01`
- Frozen main: `66822a57d2bc05082c6b82aa0b02bf7762dba98b`
- New branch: `research/belief-external-drift-wslc-portability-20261003`
- Additive result path: `research/analysis/belief_external_drift_wslc_portability_20261003/`

## H / T / D / C / U

**H.** The exact candidate, fixture, and independent raw-only auditor from the merged #5368 T0 produce byte-identical candidate/baseline output and the same 9/9 audit disposition when executed under the cached WSLc Python image.

**T.** Bind the original frozen source read-only and use the pinned `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` image (linux/amd64). A small frozen entrypoint stages exact-hash source copies into the disposable container filesystem, executes the candidate once, and writes outputs only to a unique writable result mount. If the candidate exits 0 and its files are retained, invoke a second disposable container for the raw-only auditor once. Network is disabled; no model, GUI, input, GPU, external effect, Docker Engine, or benchmark is used.

**D.** `PASS_PORTABILITY_SCOPED` only if all three candidate/baseline JSONL outputs are byte-identical to the preserved Windows-host outputs; the independent auditor exits 0 and reproduces the same audit JSON byte-for-byte; it reports 9/9 rows, zero errors, zero unsafe admissions, and 4/4 mutation detections; all source hashes match before and after staging; and both container invocations return 0. Any mismatch is retained as the first outcome; no retry or replacement allocation. A pre-candidate gate failure is STOP, not a scientific failure.

**C.** The original workload uses deterministic standard-library Python and no OS-specific interfaces, so output equivalence is expected. A single exact-source replay is a narrow portability check, not evidence that a repository-wide launcher migration is worthwhile.

**U.** No iteration-time, peak-RSS, memory-pressure, Docker comparison, resource-limit enforcement, live GUI, event-rate, source-trust, model, action-safety, or operational benefit is tested. WSLc's configured memory option is not treated as a kernel-enforced cap. The result applies only to this finite synthetic workload and exact image/source pair.

## Resource snapshot and scope

At preregistration, WSL software/WSLc were 3.0.1.0, Ubuntu was WSL2, and `wslc ps` showed zero running containers plus three already-exited containers, all left untouched. Docker CLI was absent. Ubuntu reported Python 3.12.3; the pinned image carries Python 3.12.14. Fourteen unrelated `native_mcp_v1.py` processes were visible for `results-local/native-host-integration-03` (seed 991315). The host snapshot showed about 5.0 GB `MemAvailable`, zero memory PSI, and no finite root cgroup memory/swap limit. No performance or memory sample will be collected, and no existing process or container will be touched.

This bounded functional replay is separate from #6389's native-WSL2 comparison and #6693's same-host Docker-versus-WSLc cost experiment. It does not release, consume, or modify either allocation or their artifacts. It uses the user's explicit WSLc direction but makes no claim that WSLc has an exclusive host resource lane.

## Frozen commands

Run from the repository root in PowerShell after the freeze commit. Both output directories must be new and empty. The candidate output is retained before the auditor starts.

```powershell
$source = (Resolve-Path 'research/analysis/belief_external_drift_5368_t0_20261003').Path
$package = (Resolve-Path 'research/analysis/belief_external_drift_wslc_portability_20261003').Path
$candidateOut = (Resolve-Path "$package/formal/candidate").Path
$auditOut = (Resolve-Path "$package/formal/audit").Path
$image = 'python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f'

wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M `
  --volume "${source}:/source:ro" --volume "${package}:/pkg:ro" `
  --volume "${candidateOut}:/out:rw" --workdir /pkg `
  $image python -B /pkg/run_wslc.py candidate
if ($LASTEXITCODE -ne 0) { throw 'Candidate STOP/FAIL; do not retry or start auditor.' }

wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M `
  --volume "${source}:/source:ro" --volume "${package}:/pkg:ro" `
  --volume "${candidateOut}:/input:ro" --volume "${auditOut}:/out:rw" `
  --workdir /pkg $image python -B /pkg/run_wslc.py audit
```

The `512M` option is an accepted request only; no hard memory-limit claim is made. Candidate and auditor invocations are each exactly one. No Docker/Podman, WSL distro shutdown, container cleanup, or shared-process action is in scope.
