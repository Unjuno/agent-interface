# Issue #4986 Stage 1 — atomic publication reader/writer construction

## H / T / D / C / U

**H.** With a fixed inert role-skill package and a candidate whose only changes are generation/provenance metadata, same-directory os.replace after validation yields only complete ACTIVE generations to concurrent readers. A deliberate in-place diagnostic should expose a torn package; a digest-invalid candidate must be rejected without changing ACTIVE.

**T.** Allocation needle-role-skill-active-candidate-boundary-stage1-v1, Issue #4986. Main intake SHA 2dadbde96a3774614f0dff8b51f95dbef9d05716; branch research/needle-role-skill-publication-stage1-4986-20260928; additive path research/system1/needle_role_skill_publication_stage1_4986_20260928/. Exact baseline is #3890 seed-3788 role-skill JSON, Git blob 45b80150dac503f4eb6f3cb5d82f9afa2c587107, normalized SHA-256 2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a. The mounted local copy is 15,280 bytes with SHA-256 a36a3391df3765e77fc894c213d5be2f029e6cc68e664985c23c628b15ad4e2d; runner strips exactly one terminal LF and verifies the normalized 15,279-byte source digest. Candidate generation 3789 changes only generation/provenance seed; all tensors remain value-identical.

One publisher and four concurrent reader threads perform a fixed five-phase schedule (20 raw observations): baseline; candidate fully staged/fsynced while ACTIVE is still old; after atomic replace; an explicitly unsafe in-place half-write diagnostic; and after that diagnostic write completes. Validation-to-publication delay is fixed at 10 ms. A tampered-candidate control must reject and preserve the exact ACTIVE SHA before and after. This is one Linux/amd64 local Docker construction run and one distinct raw-only audit; no training, model inference, provider, GUI, user data, or authority.

**D.** PASS_ATOMIC_PUBLICATION_CONSTRUCTION_SCOPED only if the independent audit reconstructs all 20 scheduled observations; every safe-path observation is exactly the expected complete generation; the unsafe midpoint is invalid/incomplete; the completed diagnostic write is the exact candidate; the invalid candidate is rejected with equal before/after ACTIVE hashes; source and raw hashes match; no runner or audit errors occur. Pre-run failure is a typed STOP; integrity mismatch is STOP_INDEPENDENT_AUDIT. One invocation per runner/auditor; no retries, seed replacement, or post-result threshold changes.

**C.** Four threads in one process, one publisher, one host, one small hand-authored JSON fixture, one fixed 10 ms delay. This does not test process crashes, power loss, cross-process memory ordering, concurrent model inference, update throughput, Windows-native rename semantics, or real skill correctness. The deliberate in-place write is a diagnostic contrast only.

**U.** Construction/system boundary only: not learned Needle competence, real-time fine-tuning, natural-language role routing, task utility, production safety, performance, or deployment readiness. No training allocation or optimizer step is consumed.

## Frozen commands (PowerShell)

Runner; source is read-only and raw output must be a separately pre-created empty directory:

```powershell
docker run --pull=never --rm --network=none --read-only --cpus=0.25 --memory=256m --pids-limit=32 --tmpfs /tmp:rw,nosuid,nodev,size=16m --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\goal-unjuno-agent-interface-github-mcp-6\scratch\needle-role-skill-active-candidate-boundary-4986,target=/src,readonly" --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\goal-unjuno-agent-interface-github-mcp-6\scratch\needle-role-skill-active-candidate-boundary-4986\stage1_raw,target=/out" --workdir /src python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 python -B reader_writer_v1.py
```

Independent auditor, in a second container:

```powershell
docker run --pull=never --rm --network=none --read-only --cpus=0.25 --memory=256m --pids-limit=32 --tmpfs /tmp:rw,nosuid,nodev,size=16m --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\goal-unjuno-agent-interface-github-mcp-6\scratch\needle-role-skill-active-candidate-boundary-4986,target=/src,readonly" --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\goal-unjuno-agent-interface-github-mcp-6\scratch\needle-role-skill-active-candidate-boundary-4986\stage1_raw,target=/raw,readonly" --mount "type=bind,source=C:\Users\junny\Documents\Codex\2026-09-19\goal-unjuno-agent-interface-github-mcp-6\scratch\needle-role-skill-active-candidate-boundary-4986\stage1_audit,target=/out" --workdir /src python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 python -B audit_reader_writer_v1.py
```

Image ID: sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9, linux/amd64. Local engine was read as Docker 29.8.0 linux/x86_64 before freeze. Exact runner/auditor hashes and GitHub blob IDs are in FREEZE.json.

## Evidence files

- FREEZE.json: immutable source, input, image, schedule, resource envelope, outcomes and scope.
- reader_writer.py, audit_reader_writer.py: frozen runner and independent auditor.
- raw/raw.json, audit/audit.json: reserved evidence names for the one-shot outputs.
