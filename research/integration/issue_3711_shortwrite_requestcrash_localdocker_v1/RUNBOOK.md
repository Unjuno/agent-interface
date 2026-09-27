# Frozen runbook — Issue #3830 formal-01

Base commit: `3fa567baa277d1bfdfe415e522b419e6414d7c26`
Image: cached `python:3.12-slim-bookworm`; resolve and record immutable local image ID/digest before run. Freeze SHA256SUMS of runner, auditor and fixture before the sole invocation. Source is read-only; output is a fresh isolated writable directory.

From PowerShell, set ISSUE3830_SOURCE to a byte-for-byte source bundle and ISSUE3830_OUT to a freshly created empty result directory. Resolve paths first. Run once:

```powershell
$source = (Resolve-Path $env:ISSUE3830_SOURCE).Path
$out = $env:ISSUE3830_OUT
$img = docker image inspect python:3.12-slim-bookworm --format '{{.Id}}'
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --mount "type=bind,source=$source,target=/src,readonly" --mount "type=bind,source=$out,target=/out" --entrypoint python $img /src/runner.py --source-dir /src --result-dir /out
```

Then run the independent auditor on host with source and result paths. Corruption challenges use disposable copies only; baseline raw bytes are immutable. No network, package installation, GPU, model/GUI/input, cleanup/prune, or retry. Failure or ambiguity consumes formal-01; a changed harness requires a new successor.
