# Issue #3926 allocation-03 branch-tip archive

This additive archive preserves the branch-specific allocation-03 preregistration,
construction STOP/PASS records, frozen package, and one-shot runner from
`research/issue-3926-dockerdesktop-engine29-v1` at tip
`28bbb4fe8af03a28b3086de5b1147a89d7e03c6f`.

The eight archived blobs match that branch exactly. The other 17 files in its
study subtree were byte-identical to the corresponding files on main at
recovery time. The branch's `PREREGISTRATION.md` differs from the current main
version, so its frozen copy is retained here rather than overwriting the current
allocation record. This is a source fragment archive, not a runnable allocation
directory; the original remote branch remains the authoritative, intact freeze.

Allocation `dockerdesktop-20260926-03` was frozen `NOT_STARTED`. The latest
Issue #3926 environment check reports that this host has only OrbStack
29.4.0/linux/arm64 and no Docker Desktop context, while the allocation requires
Docker Desktop Engine 29.8.0/linux/x86_64 and the pinned cached Python image.
That is `STOP_FROZEN_ENGINE_CONTEXT_UNAVAILABLE`; do not substitute OrbStack or
invoke the formal suite/auditor. No formal invocation, result, or scientific
claim is added by this archive.

Construction 05's STOP and construction 06's fake-only PASS are retained as
separate historical records. They are not pooled with formal evidence. Source
branch and recovery artifacts are preserved; no source, freeze, or prior
allocation was edited or rerun.

| Archived file | Original Git blob |
|---|---|
| `PREREGISTRATION.md` | `3ff8f9de7aee9a391beb9149002db458a6f49619` |
| `construction/05/STOP.md` | `9e104a3bf420ea75cf3a00392c7844123d8c16e6` |
| `construction/06/container-inspect.json` | `6118de307a22105979f5585445c237ff5ae83e55` |
| `construction/06/output/construction.json` | `a17ff9f5cbadb2736bec5e35e83777bc570940c7` |
| `construction/06/output/fake-capture.json` | `154f11c8360b82f5eebb3cd2080536e0b930b96f` |
| `construction/06/probe.py` | `2ef6ed27d5a06f94302ee53318a7d938219e77a4` |
| `formal/dockerdesktop-20260926-03/FREEZE.json` | `d30e547e00d09a7cca9918533b718b24351b9af5` |
| `run_allocation03.ps1` | `6017427625b1109a622f5eada0c98923a60f0b52` |
