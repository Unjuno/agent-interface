# Retained STOP — private WSLc session was not found

## Frozen allocation

Follow [PROTOCOL.md](PROTOCOL.md). Frozen base is `0db00a564daff64e47fd6931954ace0f71ab8f2b`, branch `migration/wslc-isolated-session-smoke-20261005`, pinned Python digest `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`. The one planned session name was `ai-wslc-d3484fa5c43d44049228762c850c8257`, with unique proposed storage path `C:\Users\junny\AppData\Local\Temp\agent-interface-wslc-session-66c5dc28b5bf4028a53ffe48c7696a60`.

## First outcome

Preflight observed zero live `wslc.exe` clients and 7,048,224,768 bytes free on C:. WSL is 3.0.1.0; Ubuntu is running as a WSL2 distro. The task-local Git worktree is clean relative to its frozen main base except for this additive evidence package. A previous read-only snapshot had seen four exited WSLc containers, but their owners were never identified; this attempt issued no default-session or global container inventory operation.

One invocation was made:

```powershell
wslc.exe system session enter 'C:\Users\junny\AppData\Local\Temp\agent-interface-wslc-session-66c5dc28b5bf4028a53ffe48c7696a60' --name ai-wslc-d3484fa5c43d44049228762c850c8257
```

It exited 1 in 1.398 seconds before opening a session shell. Raw stderr (Japanese Windows localization):

```text
'C:\Users\junny\AppData\Local\Temp\agent-interface-wslc-session-66c5dc28b5bf4028a53ffe48c7696a60' に WSLC セッションが見つかりません
エラー コード: ERROR_PATH_NOT_FOUND
```

Post-check: that exact path did not exist, and a read-only process snapshot still showed zero `wslc.exe` clients. No candidate container, image lookup/pull, list/inspect, shared-session operation, Docker action, stop/prune/delete, or retry occurred. Candidate runs 0; auditor runs 0; container runs 0. Only CLI help and the one frozen session-entry attempt were issued.

## Classification and limits

**Disposition:** `STOP_SESSION_STORAGE_NOT_FOUND`; the intended portability experiment is **not evaluated**. The CLI rejected the supplied storage path; this does not show that WSLc generally fails, that containers cannot run, or that Docker is required. The current evidence does not establish whether `session enter` requires pre-existing WSLc storage/session material, a particular path convention, or another prerequisite. Do not repeat the consumed allocation. Any corrected attempt must be separately frozen with a verified, isolated session-creation path; preserve this STOP unchanged.

No speed, Docker parity, memory-relief/OOM, CI migration, GUI, or application claim follows. The accepted memory option is not independently enforced here; prior WSLc host reports warn that swap/cgroup limits may be unavailable.
