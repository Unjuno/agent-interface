# Issue #6329 WSLc allocation-10 — preparation record

Status: `PREPARED_DEFERRED_UNASSIGNED`. No formal candidate, CUDA worker, auditor, or WSLc container has run for this allocation.

## Scope

Test bounded coexistence of six independent CUDA processes on the same RTX 3080, each holding 192 MiB and completing 20 deterministic int64 increments, while preserving at least 4 GiB globally free VRAM. This is not a performance benchmark or an Agent Interface/model result.

## Runtime correction

This new allocation uses native Microsoft WSL Containers (`wslc.exe`), not the Podman/crun runtime frozen by allocation-09. The prior terminal pre-candidate STOP and all its bytes remain unchanged. The package is based on current main `5863696c67338d380820faa4ba1a866e0d25719b`. The exact PyTorch image digest and local image ID were inspected in WSLc's cache; no pull or image mutation occurred. WSLc CLI supports GPU pass-through, network isolation, CPU/memory bounds, unprivileged UID, and bind mounts, but not a read-only rootfs or PID-limit option. WSLc cgroup/swap limitations will be retained as explicit limitations.

## Construction evidence

Host-only standard-library construction suite: 9/9 passed, covering six-worker checksum reconstruction, malformed/duplicate worker rejection, memory thresholds, the four frozen mutation controls, and independent host telemetry parsing. Python AST parsing passed. These tests are preparation only; no CUDA call or container run is implied.

## Resource and invocation status

The package has no assigned GPU interval. The shared-GPU coordination record currently has a different pending request (#6354); this work remains deferred until that request is explicitly resolved and a single exact host-GPU assignment is recorded. Candidate=0, CUDA worker calls=0, auditor=0, retries=0. The expected sequence is one WSLc candidate, then one separate WSLc CPU-only raw auditor only on candidate exit 0.

After rebasing the preparation branch to the next main commit, Windows Git autocrlf materialized the Python/PowerShell source as CRLF in the working tree. The code semantics were unchanged; the formal-runner hash gates the exact current working-tree bytes recorded in `FREEZE.json`, which are the bytes mounted into WSLc.
