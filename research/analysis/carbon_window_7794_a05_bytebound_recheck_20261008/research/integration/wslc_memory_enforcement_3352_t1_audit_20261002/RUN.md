# Audit-only run record

Allocation: `WSLC-MEMORY-CAP-3352-T1-AUDIT-20261002-01`  
Issue: #6355; predecessor: #6309 / #3352  
Candidate/probe invocation in this allocation: **0**  
Independent auditor formal invocations: **1**  
Formal retries: **0**

## Original evidence packet

The input is the exact original local packet retained in the shared workspace, not a line-ending-normalized reconstruction from the GitHub Contents API. Its four SHA-256 values match its included `SHA256SUMS.txt`; GitHub-published PR #6309 copies are preserved separately and have distinct byte content as documented in `REPORT.md`.

Input files and their mount: `wslc-memory-t0/` on the Windows host, bound read-only to `/inputs`. Auditor source is bound read-only to `/auditor.py`. Output directory `_out_6355_wslc_memory_audit_20261002/` is a distinct writable mount at `/output`.

## Construction

Ubuntu WSL, Python 3.12.3:

```text
python3 -B -m unittest discover -s /mnt/c/Users/junny/Documents/Codex/2026-09-19/unjuno-agent-interface-x20/_scratch_6355_wslc_memory_audit_20261002 -p test_auditor.py -v
```

Result: 6 tests, all passed. Exact captured output: `results/construction/CONSTRUCTION.log`.

## Preflight and formal command

First exact multi-mount preflight returned WSL `E_FAIL` before auditor execution; a no-mount smoke on the same image then returned `WSLC_SMOKE_READY`, exit 0. The separately authorized exact mount-only preflight subsequently returned `READY`, exit 0. Full incident history and commands are in `PRE_FORMAL.md`. No candidate or audit outcome was examined during preflight.

Formal command, executed exactly once in PowerShell:

```powershell
wslc run --rm --pull never --network none --cpus 1 --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\wslc-memory-t0,target=/inputs,readonly" --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\_scratch_6355_wslc_memory_audit_20261002\auditor.py,target=/auditor.py,readonly" --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\unjuno-agent-interface-x20\_out_6355_wslc_memory_audit_20261002,target=/output" python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /auditor.py /inputs /output/audit.raw.json
```

Formal exit: **0**. Complete launcher stdout/exit record: `results/formal-01/launcher.log`. The container was disposable (`--rm`); post-run `wslc container list --all` showed only the previously existing exited smoke container `adadf5c4bd8d`, not this audit container. No memory limit was requested for this low-memory parser; this run makes no resource-cap claim.

## Raw result

`results/formal-01/audit.raw.json` is 1,048 bytes, SHA-256 `72958F62459E99D1770F648553267C8CE4F2299A191AE9B6CB5833468FEC319F`. It reports `PASS_INDEPENDENT_AUDIT_SCOPED`, two arms, expected memory.max values, both warnings, both 384 MiB allocations, exit 0 in each recorded arm, source hash match, and identical command configurations other than requested memory.
