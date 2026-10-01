# Issue #5504 — T0-02 runner-repair successor allocation

## Why this is a new allocation

`issue5504-cegar-t0-01` is retained as `STOP_RUNNER_FREEZE_SCHEMA_KEY_ERROR`; the candidate entrypoint ran once, computed a result in memory, then exited before writing output because it read `freeze["image_digest"]` instead of `freeze["container"]["image_digest"]`. No auditor ran and no candidate result was persisted. The original freeze and STOP are immutable. This is a runner/evidence repair, not a change to the hypothesis, corpus, arms, oracle, gates, or scientific interpretation.

T0-02 has a new allocation ID, new freeze file, dedicated empty `results/t0-02/` output directory, and corrected candidate/audit entrypoints. It is not a retry or replacement of T0-01. Any runner/source hash mismatch or output collision is STOP; candidate and auditor each have one invocation, with no retries or tuning.

## H/T/D/C/U and gates

H/T/D/C/U and all scientific decision thresholds remain exactly those in [`PLAN.md`](PLAN.md). T0-02 changes only how the already frozen experiment writes and verifies its result envelope. The candidate entrypoint must emit the frozen allocation ID and nested container image digest; the separate auditor verifies these identities and independently replays all decision, lineage, metric, authority, and UNKNOWN gates.

## Commands

Construction suite (not formal evidence):

```powershell
docker run --rm --network none --read-only --mount "type=bind,source=C:/.../work/5504-cegar-t0,target=/work,readonly" --tmpfs /tmp:rw,noexec,nosuid,size=32m -w /work python:3.12.10-slim@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db python -B -m unittest -v
```

Formal candidate and independent auditor use separate containers, the read-only source mount, network none, read-only root, tmpfs `/tmp`, and the dedicated writable `results/t0-02` mount. Execute `python -B run_candidate_t0_02.py` exactly once, then `python -B run_audit_t0_02.py` exactly once only after candidate exit 0. Preserve any failure at its first disposition.
