# Result — #5368 WSLc portability replay

**Disposition: `PASS_PORTABILITY_SCOPED`.** The frozen #5368 T0 candidate and independent raw-only auditor ran successfully once each in WSLc, and every candidate/baseline output plus the audit JSON is byte-identical to the preserved Windows-host result. This is runtime-portability evidence for one finite synthetic workload, not a new safety or utility result.

- Parent: [Issue #5368 — Action-conditioned belief contracts](https://github.com/Unjuno/agent-interface/issues/5368); original T0 is preserved at [`belief_external_drift_5368_t0_20261003/`](../belief_external_drift_5368_t0_20261003/), merged by PR #6972.
- Allocation: `belief-external-drift-5368-wslc-portability-20261003-a01`.
- Preregistration/freeze commit: `2b9587860fe3ccc6d852350fbf5281a034915d4d`.
- Runtime: WSLc 3.0.1.0; pinned `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, linux/amd64, Python 3.12.14; network disabled; candidate and auditor each ran once with one requested CPU.

The candidate and auditor both exited 0. The independent raw-only auditor reconstructed **9/9** rows with zero errors and reproduced the parent audit exactly: **2** candidate admissions, **0** unsafe admissions, both safe controls admitted, **7** sticky-baseline false admissions, both safe controls refused by the age-only baseline, and **4/4** mutations detected. No authority or effect was emitted. All staged-source hashes and all four output hashes match the frozen parent result.

WSLc printed this warning on both invocations: `wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` It is preserved verbatim in [`RUN.json`](RUN.json). The configured `--memory 512M` value is recorded only as a request; no memory-limit enforcement, swap-limit, RSS, or memory-pressure claim is made. No timing was collected.

## H / T / D / C / U

- **H:** Supported only for the exact frozen source/image pair: WSLc reproduces the original host candidate/baseline bytes and raw-only audit disposition.
- **T:** One candidate invocation and, after its successful retained output, one independent auditor invocation; no retries. The container received read-only source mounts, a read-only candidate input for audit, exclusive result outputs, and no network.
- **D:** `PASS_PORTABILITY_SCOPED` because both invocations exited 0, all three candidate outputs and the audit JSON match the preserved parent SHA-256 values, and the audit reproduces all 9 rows, zero errors/unsafe admissions, and 4/4 mutation detections.
- **C:** The deterministic standard-library workload may be portable by construction; this check does not establish that WSLc is preferable for other workloads or that a migration improves iteration speed or resource use.
- **U:** No Docker comparison, speedup, iteration time, RSS, memory-pressure, hard memory cap, repository-wide launcher migration, GUI, model, external effect, or operational-safety result. The finding is limited to these frozen files and this image digest.

The separate #6389 native-WSL2 lane and #6693 Docker-versus-WSLc cost comparison are not altered or resolved by this replay. The source/result pair, warning, exit codes, and hashes are retained in this directory; the original result remains unchanged.
