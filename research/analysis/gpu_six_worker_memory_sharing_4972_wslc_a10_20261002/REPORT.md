# Issue #6329 WSLc allocation-10 — preparation record

Status: `PREPARED_DEFERRED_UNASSIGNED`. One standalone CPU-only WSLc construction preflight is retained in `construction-preflight-20261002-01/`; it is preparation evidence, not the in-window formal construction gate. No formal candidate, CUDA worker, or formal auditor has run.

## Scope

Test bounded coexistence of six independent CUDA processes on the same RTX 3080, each holding 192 MiB and completing 20 deterministic int64 increments, while preserving at least 4 GiB globally free VRAM. This is not a performance benchmark or an Agent Interface/model result.

## Runtime correction

This new allocation uses native Microsoft WSL Containers (`wslc.exe`), not the Podman/crun runtime frozen by allocation-09. The prior terminal pre-candidate STOP and all its bytes remain unchanged. The package is based on current main `a4caf65a773d37db516774b797e1244dc9e956e5`. The exact PyTorch image digest and local image ID were inspected in WSLc's cache; no pull or image mutation occurred. WSLc CLI supports GPU pass-through, network isolation, CPU/memory bounds, unprivileged UID, and bind mounts, but not a read-only rootfs or PID-limit option. WSLc cgroup/swap limitations will be retained as explicit limitations.

## Construction evidence

The host-only standard-library suite passed 10/10 after adding a regression test for the formal helper's frozen source-hash schema. A separate, standalone WSLc CPU-only preparation call at 2026-10-02 01:13:23 UTC passed the same 10 tests and verified the UID 65534 writable output bind. Its raw stdout/stderr, exit status, post-run empty container inventory and image identity are retained under `construction-preflight-20261002-01/`. An independent host-side receipt audit first produced a false negative due to its parser expecting a combined `repo@digest` token; that audit output is preserved. The corrected auditor rechecked the same raw receipts and passed with zero errors. The formal start helper still requires a fresh in-window construction gate after exact assignment/current-main refreeze; this preflight is not candidate or CUDA evidence.

## Resource and invocation status

The package has no assigned GPU interval. The shared-GPU coordination record currently has another pending GPU need; this work remains deferred until that request is explicitly resolved and a single exact host-GPU assignment is recorded. Formal candidate=0, CUDA worker calls=0, formal auditor=0, retries=0. The expected formal sequence remains an in-window WSLc construction gate, one WSLc candidate, then one separate WSLc CPU-only raw auditor only on candidate exit 0.

After rebasing the preparation branch to the next main commit, Windows Git autocrlf materialized the Python/PowerShell source as CRLF in the working tree. The code semantics were unchanged; the formal-runner hash gates the exact current working-tree bytes recorded in `FREEZE.json`, which are the bytes mounted into WSLc.
