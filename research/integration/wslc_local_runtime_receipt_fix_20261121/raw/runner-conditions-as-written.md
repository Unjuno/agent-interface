# Frozen conditions — WSLc read-only bind smoke

- Freeze time: 2026-11-21 12:21 UTC.
- Source: current main at $main; exact script SHA-256 $scriptHash; bounded-process module SHA-256 $moduleHash.
- Host: PowerShell 7.6.9 on Windows; WSLc 3.0.5.0 (C:\Program Files\WSL\wslc.exe); read-only process snapshot at 12:19:50 UTC observed zero wslc.exe processes.
- One-shot command: run 	est_wslc_local_runtime.ps1 with CLI timeout 10 s, run timeout 90 s, cleanup timeout 15 s.
- Fixed image: python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f; --pull never, --network none, --rm, --cpus 1, requested --memory 512M, and one GUID-named read-only bind mount.
- The script generates unique container name/CID file and verifies cleanup with an exact-CID filter only. It does not enumerate unrelated containers. On timeout or uncertain cleanup it preserves its unique probe directory; no retry is allowed.
- Outcome criteria: PASS only if the pinned image runs without pull/network, mounted sentinel bytes match, writes fail with EROFS, command exits 0, and exact-CID cleanup is confirmed. Any missing image or uncertain timeout/cleanup is HOLD. Memory flag acceptance is not treated as a hard-limit result.
- Scope: one local compatibility smoke, not computer-control task success, Docker parity, performance, memory isolation, or product completion. No Docker API, Docker Desktop, container inventory, WSL restart, model, or provider call.