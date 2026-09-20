# Independent audit successor 03 — preregistration

Allocation: `issue3752-request-temp-crash-audit-successor-03`.

## Obstac record

The formal allocation-02 runner passed once and its raw artifacts are retained under `formal-02/`. Before invoking the frozen audit-v2 script, static inspection showed it writes `audit.json` inside the evidence input directory. That contradicts the preregistered audit requirement that formal evidence be mounted read-only and audit output be separate. The auditor was not run; no audit failure is implied. The formal experiment was not repeated. This audit successor writes only to a distinct output mount.

## H / T / D / C / U

- **H:** Independently recomputing source/runner identities, raw-result hash, request-temp bytes and hash, both status JSON/exit codes, public CLI refusal, exact fixture hashes and complete run-directory snapshots will agree with formal-02 raw evidence and yield `PASS_AUDIT_V3` without writing to the evidence mount.
- **T:** Run frozen `audit.py` once in a fresh pinned Docker container. Mount the repository source read-only, formal evidence read-only, and a separate newly created empty results directory writable. The auditor reconstructs the expected partial request bytes for `/out/attempt/images`, inspects the actual evidence tree, and hashes the frozen source/runner and synthetic inputs.
- **D:** PASS only if every independent check succeeds and `audit.json` is written solely to the separate result mount. Any evidence contradiction is FAIL_AUDIT_V3. Missing/mismatched setup or write outside result mount is STOP. No retries under this identity.
- **C:** OrbStack Docker linux/arm64, pinned Python image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, network none, root read-only, source and evidence read-only, fresh bounded output, tmpfs, one CPU/512 MiB/PID bound/capabilities dropped/no-new-privileges.
- **U:** Artifact-level independent audit of this one scoped allocation only; not a second experiment or broader durability/adoption claim.

Frozen auditor Git blob SHA-1: `4e4716e69899cb45ff66330c36bbec33cccb29d5`; SHA-256: `b8514728b1d4af77d00e0e860e9d466e74f5fde4ce27785c5d8541b1ebe1ff71`. Formal raw SHA-256: `6d0cc630d979b19263450f8220ac0bce184e0ebdc5ea267ab76f67d1e994ea68`.

The audit may run only after this plan/script are committed, hashes are posted to Issue #3752, and immediately-pre-run mount/image/output checks pass.
