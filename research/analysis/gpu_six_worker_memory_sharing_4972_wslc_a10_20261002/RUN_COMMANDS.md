# Formal WSLc sequence — allocation-10

This is a one-shot recipe. Do not run without an exact coordinator assignment for this allocation. A request, idle GPU snapshot, elapsed window, or another issue's release is not a lease.

## Human start gate

1. Read Issue #5085 and #6329 at launch. Confirm an exact coordinator-assigned physical-host RTX interval for allocation-10 and verify no competing active GPU/WSLc owner or unknown process. #6354's request must have an explicit disposition first. Never infer availability from the clock alone.
2. Read current main SHA; it must equal `FREEZE.json`. The helper rechecks this with `git ls-remote` and stops if main moved.
3. Confirm no branch/path/PR/output collision, no running or unknown-owned WSLc container, cached exact PyTorch digest/ID/platform, and current WSLc 3.0.1.0. The helper verifies the main/image/inventory/output gates and exact coordinator comment URL/time interval.
4. Query the Windows-host RTX 3080 with `nvidia-smi`; identity must match and free VRAM must be >=10 GiB. Inspect the process list and resolve ownership. Unknown owner or unstable capacity means STOP. Do not stop or alter another process/container.
5. Run the standard-library construction suite before the formal window. These host-only tests do not invoke CUDA or a container.

## Invocation

Invoke the script exactly once using the exact comment URL and UTC interval assigned to this allocation:

```powershell
.\run_formal.ps1 `
  -LeaseRecord 'https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-<exact-id>' `
  -LeaseStartUtc '<assigned-start-ISO-8601-Z>' `
  -LeaseEndUtc '<assigned-end-ISO-8601-Z>'
```

The script captures a separate Windows-host `nvidia-smi` CSV sampler at 1 Hz; it launches one WSLc candidate with network disabled, GPU pass-through, the exact cached digest, unprivileged UID, read-only source/sample binds and a fresh candidate-output bind. It records exact argv, stdout/stderr, exit code, initial GPU/inventory/image/main snapshots and the coordinator lease reference. The candidate has six spawned GPU workers, a six-way barrier, 20 integer increments and a bounded 110-second worker deadline.

Only after candidate exit 0 and a fresh empty WSLc inventory check does the script launch a separate WSLc CPU-only, network-disabled raw auditor. Candidate or auditor nonzero exits are terminal for this allocation; retries and seed substitution are forbidden. If the candidate exits nonzero, auditor is skipped. If an owned/unknown container remains, do not stop or delete it; preserve evidence and report HOLD/STOP.

The WSLc CLI does not expose rootfs-read-only, PID-limit or swap-limit enforcement. The invocation does not claim those controls. It uses no secrets, no network, source/sample read-only mounts, one unique writable output mount, unprivileged UID, CPU/memory bounds, and `--rm`; retain any runtime cgroup/swap warning verbatim.
