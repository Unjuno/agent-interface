# WSLc memory-cap retained-receipt independent audit

Disposition: **PASS_INDEPENDENT_AUDIT_SCOPED** for the predecessor's recorded local receipt.

## Relationship and preserved history

This audit-only successor (#6355) follows open #6309 / #3352. It does not rerun the memory-allocation probe, alter its outcomes, or change PR #6309. Original local evidence and the separately published PR #6309 copies are both retained byte-for-byte under `inputs/` to make a discovered publication-fidelity difference inspectable rather than silently replacing either version.

## H / T / D / C / U

- **H:** An independently implemented standard-library parser can validate the retained local command pair, source digest and raw output. The 512M control and 128M constrained run should both report their requested `memory.max`, the cgroup/swap warning, 384 MiB allocated and exit code 0; all other command options should match.
- **T:** Exactly one WSLc audit-only formal invocation against the original local evidence packet, pinned Python image digest, no network, one CPU, read-only input/auditor mounts and a distinct writable output mount. The probe was read as bytes only; it was never imported or executed. Construction tests ran natively in Ubuntu WSL before the formal audit.
- **D:** **PASS_INDEPENDENT_AUDIT_SCOPED.** The predecessor SHA256SUMS matches all four original local evidence files; the probe SHA-256 equals the source digest in both raw arms; exactly two otherwise-identical commands differ only in requested memory (512M/128M); both raw arms report 536870912/134217728, each includes the warning and `cgroup 0::/`, both allocate 384 MiB and exit 0. The independent auditor's six construction tests passed 6/6; its one formal run exited 0 and emitted the retained audit JSON.
- **C:** WSL package 3.0.1.0 / WSLc 3.0.1, Ubuntu 24.04 on WSL2 kernel 6.18.40.1-microsoft-standard-WSL2, cached `python:3.12-slim` digest `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, linux/amd64. Prior raw merged stdout and stderr.
- **U:** This is a text/raw receipt audit, not proof of effective cgroup enforcement, peak RSS, swap behavior, OOM behavior, reduced memory pressure, faster iteration, Docker parity, or representative roadmap behavior. It does not satisfy #3352 closure.

## Publication-fidelity finding

The exact local files reproduce the predecessor manifest. The published PR #6309 files are not byte-identical to that packet: for example, published commands replace the absolute read-only source path with a placeholder, published raw.log omits both echoed `$ wslc run ...` command lines, and the published report/raw/source lengths differ. Their exact Git blob identities and contents are retained separately under `inputs/published-pr6309/`; this successor preserves the discrepancy and does not rewrite PR #6309 or its history. PR #6309 should remain Draft until its owner decides how to repair or qualify the source-publication boundary and the separate representative-workload gate is addressed.

## Reproduction and evidence

- Exact auditor, construction source and output: see `auditor/` and `results/`.
- Exact invocations, preflight incident/recovery, and environment: `RUN.md` and `PRE_FORMAL.md`.
- Frozen identities and package hashes: `FREEZE.json` and `SHA256SUMS.txt`.
