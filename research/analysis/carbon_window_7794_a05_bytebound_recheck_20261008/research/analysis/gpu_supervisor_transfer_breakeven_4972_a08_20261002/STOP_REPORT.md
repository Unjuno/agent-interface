# Terminal pre-candidate STOP

Recorded UTC: 2026-10-01 23:50:44 UTC
Issue: #6322
Allocation: GPU-SUPERVISOR-TRANSFER-BREAK-EVEN-4972-20261002-08
Seed: 49720261008
Disposition: `STOP_PRE_CANDIDATE_NO_GRANTED_NONOVERLAPPING_GPU_WINDOW`

## Counts and scope

Formal candidate invocations: 0. CUDA candidate calls: 0. Fits: 0. Formal auditor invocations: 0. Retries: 0. No candidate or audit result exists; this is a resource/ownership STOP, not a scientific FAIL or PASS. The frozen hypothesis, synthetic dataset, code, thresholds, and prior allocations remain unchanged. No CPU/GPU timing, model, GUI, or task-effect claim is made.

## Stop basis

- Issue #6322's 00:45–01:00 UTC interval was a request only; #5085 contains no coordinator assignment.
- The preceding #6296 owner-bound GPU interval ended at 23:40 UTC, but its issue contains no explicit completion/release. Its setup-overlap disclosures remain preserved.
- The conditional 23:40–23:45 UTC CPU-only WSLc slot on #5927 also had no recorded start/release; its start gate explicitly depended on #6296 release.
- #6321 requested 00:45–01:15 UTC on the same RTX 3080, directly overlapping A08. #6324 separately requested 01:20–01:50 UTC. #6329 records a shared-GPU request without an exact assigned interval. Requests are not grants, and WSL exposes the same physical GPU.
- At the WSL check, Arch Linux WSL 2 and rootful Podman 6.1.3/crun were available, CDI listed `nvidia.com/gpu=all`, RTX 3080 utilization was 0% with 0 MiB used, and Podman's pinned PyTorch digest store was empty. The exact PyTorch image was visible in the separate WSLc store, but substituting runtime would change the frozen execution environment. Idle telemetry and another runtime's cached image do not provide the missing lease.

Main advanced from the package's base `093b39fdab8d8cd04c422f8d9956deef1b40a692` to `c09f073f2a6e078c0fe5d8192246cc821cecc29c`. The 9 intervening commits (114 changed files in the compare response) do not touch this additive package path; the package is refrozen to current main for recordkeeping only.

## Future execution

Do not reuse this stopped allocation as if it had run. A future attempt needs a fresh successor allocation/seed, an explicitly assigned non-overlapping RTX 3080 interval, explicit prior-owner release, an exact image in the selected WSL container store, and refreshed source/output/GPU/capacity gates. Keep all counts above at zero.
