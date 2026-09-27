# Formal launch STOP 01 — XDamage temporal-boundary v2

Date: 2026-09-27 (Asia/Tokyo)
Allocation: `xdamage-temporal-boundary-3935-v2-20260927-01`
Frozen source branch: `research/xdamage-temporal-formal-v2-20260927`
Frozen head before launch: `764c84f94dd3dc86f6cb` (full commit `764c84f94dc84f498c1695572d2aa836f5f97d39`)

## Outcome

`STOP_LAUNCHER_BEFORE_RUNNER`. No formal runner invocation began; the frozen scientific allocation remains 0/1. This is an execution-wrapper failure, not a scientific result. No experimental rows, raw frames, or formal-start marker were produced. The one-shot allocation was not retried.

## Evidence

- Exact attempted command: `bash research/observation_gating/xdamage_temporal_boundary_v2/run_container.sh`
- Windows working directory: `C:\Users\junny\Documents\Codex\2026-09-19\new-chat\work\agent-interface-normalgit-4893`
- `bash` resolved to `C:\Windows\system32\bash.exe` (WSL launcher), while the command supplied a relative script path from a Windows working directory.
- Process result: exit code 1, empty stdout, empty stderr.
- The `results` output tree was absent; no formal marker or STOP record from `run_formal.py` existed.
- `docker ps -a --filter ancestor=agent-interface-gtk-preflight:local` returned no container.
- The pinned image itself was present and had the frozen ID `sha256:e2a7634d2b9627ec037c488d6aa472c6c00d5ef0dda6e302f7dced8b9b8752d4` (`linux/amd64`).
- Before this launch, in a separate bounded, network-disabled container, freeze verification passed for 7 source files, all 7 protocol tests passed, and Python syntax compilation passed. GitHub MCP readback matched the frozen file blobs; main's O1 source blob matched `d2629bc94d40cc0a8e1bf9e053585549218629ed`.

## Interpretation and disposition

The failure occurred at the host shell/working-directory handoff before evidence of container or runner startup. It provides no evidence for or against XDamage behavior. The formal allocation stays unconsumed at the runner level, but the preregistered no-retry rule is honored: no alternate shell or direct Docker launch was attempted. This stop is retained for review and must not be cited as PASS, FAIL, or HOLD on the scientific hypothesis.

GPU was not used. The tested XDamage server/notification mechanism has no GPU-dependent treatment; the requested GPU preference was considered and documented in Issue #4893.
