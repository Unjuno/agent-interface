# Allocation 01 — execution preflight stop (2026-10-03)

## First outcome (preserved; no formal run consumed)

The first WSLc source bind-mount preflight targeted the Windows-backed workspace through `\\\\wsl.localhost\\archlinux\\mnt\\c\\...`. WSLc 3.0.1.0 returned `E_INVALIDARG` / “Access is denied”. No candidate or auditor process started.

A second transfer attempt invoked `cp` inside Arch WSL with a Windows drive-letter path; Linux correctly reported that the path did not exist. The subsequent preflight container had no source files and returned `FileNotFoundError`. This was also before any candidate or auditor invocation.

Thus the allocation remains eligible for its single preregistered candidate and auditor run. These are source-delivery/environment failures, not scientific FAIL evidence. The source files were not modified.

## Resolution

WSL has outbound HTTPS access to GitHub (`git ls-remote` succeeded). Use the frozen branch directly from within the Arch distro, in its Linux filesystem, then verify all three executable SHA-256 values against `FREEZE.json` before invoking the candidate. Keep the container offline and source mount read-only.

## Runtime caveat

WSLc emitted: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` The requested 256 MiB limit is therefore not fully guaranteed by the kernel. This warning is retained; do not represent the run as having strictly enforced memory isolation.

## Accounting

- Candidate formal invocations: 0
- Independent auditor formal invocations: 0
- Retry allowance used: 0
- Scientific outcome: NOT RUN
- Environment/preflight status: STOP, resolved by switching the source path to WSL's native filesystem
