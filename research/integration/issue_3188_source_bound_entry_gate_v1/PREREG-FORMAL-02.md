# Issue #3188 source-bound execution — successor allocation formal-02

This is a new allocation following formal-01 `STOP` before container creation. It preserves formal-01 artifacts and does not reuse its allocation identity. Candidate code, gates, source hashes, image digest, platform, and scientific scope are unchanged; only the Docker image reference changes from raw image ID to the frozen digest-verified local tag because the daemon rejected the ID syntax before creating a container.

## H/T/D/C/U

- **H:** Exact main-branch MAP01 recovery-entry gate source executed in a pinned local container emits the declared 32-vector readiness result; a separately implemented auditor reconstructs every decision/control.
- **T:** Allocation `issue3188-source-bound-entry-gate-formal-02`. Verify `python:3.12-slim` resolves to immutable image ID `sha256:2f17fc044b579bab302c2e8053d4a686e2cb9a83de48e70534b94cd8ebbe06a9`; execute the exact main `run.py` once using the local tag in a `--network none`, read-only container. Audit read-only raw in a second container. No source change, CI substitution, or retry.
- **D:** PASS only for 32 unique Boolean vectors, exactly one AUTHORIZE, independently derived current snapshot HOLD, five negative controls HOLD, all mutation challenges rejected, source/image identity and cleanup verified. Source/image mismatch or pre-result runner failure is STOP; incorrect candidate output is FAIL; incomplete retained raw is HOLD.
- **C:** Finite readiness classifier only; no MAP01 game, model, GUI, X11, input, authority grant, or recovery efficacy.
- **U:** No full workflow/CI equivalence, runtime safety, gameplay, or production claim.

## Frozen identity

- Source base: `f79ef46d478911170d73b71bddcbe58fd698dc84`.
- Frozen preregistration/source-verifier commit: `b6c0d351a83c5fe21c9a47d6b6d1e9e5a6aeafac`.
- Candidate `run.py` SHA-256: `e104bf12925ef7878e7972c768cb19ecfdfe699303667bebf0ee6a0276f05822`.
- Candidate `audit.py` SHA-256: `72a5f6dcffff0e9d3a5e2daa58937bb4ab440ca789d824f183f168abc57e458d`.
- Independent verifier SHA-256: `ffae71aa3546b552915f894fac14d29c9e5d4c7007058941b881e7233e3083d2`.
- Runtime: OrbStack Docker Engine 29.4.0, Linux/arm64.
- Image ref: `python:3.12-slim`, required ID/digest `sha256:2f17fc044b579bab302c2e8053d4a686e2cb9a83de48e70534b94cd8ebbe06a9`.
- Raw output: `results/formal-02/raw.json` (must not exist before launch).
- Formal command: `docker --context orbstack run --rm --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=16m -v <exact-main-candidate-dir>:/src:ro -v <formal-02-dir>:/out:rw python:3.12-slim python /src/run.py /out`.
- After formal only, run independent auditor in a fresh container with formal-02 mounted read-only and only `results/independent-02/` writable.
- One invocation per allocation; no same-ID retry/replacement/tuning.

## Interpretation

The expected current snapshot class is HOLD. The one AUTHORIZE row is a truth-table admissibility vector, not a live authority grant. Preserve formal-01 STOP and all historical #2345/#3188 records unchanged.
