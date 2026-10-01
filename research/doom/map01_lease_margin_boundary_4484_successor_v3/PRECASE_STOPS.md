# Preserved setup/audit stops (Issue #5062)

These are retained as execution history and are not counted as experimental cases:

1. A PowerShell-launched WSL command expanded Bash $ROOT/$OUT variables in the caller. mkdir received an empty path; no Docker container or case started.
2. A second shell orchestration attempt repeated the interpolation mistake. No case started.
3. Initial GitHub source materialization through patch application added terminal blank-line whitespace. The executable sender was the existing byte-verified source from #5054 (SHA256 edd4cea89c541d42457e8c48992d3efe1bcb0ab7610489b47e8efa60660aab3a); the production client, Lease, and server had only trailing whitespace differences from the pinned GitHub blobs. The executed code was not edited.
4. A first independent-audit container had the complete work directory mounted read-only, so writing out/audit.json raised EROFS. The container did not access the socket or rerun any cases. The successful audit run mounted source read-only and only out/ writable.

The formal server container then handled exactly 15 clock exchanges, four lease submissions, and one shutdown request, and exited 0. No retries or extra cases occurred.


