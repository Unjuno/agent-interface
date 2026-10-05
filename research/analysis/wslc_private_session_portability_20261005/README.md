# WSLc private-session portability smoke

Prospective one-shot environment test for a fresh named WSLc session and a single cached CPU container. Frozen H/T/D/C/U and stopping rules are in [PROTOCOL.md](PROTOCOL.md). No Docker comparison, resource benefit, CI migration, or general parity is inferred.

**Disposition:** `STOP_SESSION_STORAGE_NOT_FOUND`. The single `wslc system session enter` attempt failed before creating an owned session or starting a container. The exact stderr was `'<storage-path>' に WSLC セッションが見つかりません` / `ERROR_PATH_NOT_FOUND`; candidate/container runs: 0. The absent session-storage path remained absent, and the post-attempt process snapshot found zero `wslc.exe` clients. No retry, default-session access, image/container inventory, Docker operation, or cleanup was performed. See [STOP.md](STOP.md).
