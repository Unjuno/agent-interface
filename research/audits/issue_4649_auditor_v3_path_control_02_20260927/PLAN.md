# Issue #4649 — auditor-v3 path-control allocation 02

## H / T / D / C / U

- **H:** The v3 resolved-path candidate rejects traversal, input symlink escapes, and manifest symlink escapes while allowing a regular in-root file and an in-root symlink.
- **T:** One separately identified controls-only Docker allocation runs the byte-identical candidate from allocation 01 using a corrected gate harness. Required V3 error markers are checked for presence, not exact equality of the full error list, so independent ledger-mismatch diagnostics are permitted. Five synthetic cases; v1 auditor is a PASS stub. Preserve allocation 01's FAIL and raw bytes unchanged. No formal #4649 runner or prior eight-control harness.
- **D:** Scoped PASS iff the contained file and in-root symlink return `PASS_INDEPENDENT`; `../`, input symlink escape, and manifest symlink escape return structured FAIL with required error marker(s); stderr is empty; source/image identities match. Any escape accepted is FAIL, compatibility false refusal is FAIL, source/environment mismatch is STOP. One invocation only; no retries.
- **C:** Candidate `audit_v3.py` SHA-256 `7b506919f5ed0a9b6c1fe2ebd4a720ed4c2b41bf38ed8d9c6939e2fc9685863d`; corrected probe hash will be frozen below. Docker Desktop 28.5.1, cached image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64 CPython 3.12.14; no network or pull; read-only root/source; one CPU, 256 MiB, 32 PIDs; 32 MiB noexec/nosuid tmpfs; separate output mount.
- **U:** Synthetic path-ledger controls only, v1 stubbed, stable read-only fixtures, no concurrent filesystem race test and no production claim. Even a scoped PASS does not change the frozen allocation 01 FAIL or qualify the full combined v1+v3 auditor until broader integration controls are run.

Allocation: `issue4649-auditor-v3-path-confinement-20260927-02`.
