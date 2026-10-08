# Construction-01 v2 result

Status: `PASS_T1_IDENTITY_PRECEDENCE_CONSTRUCTION` for the synthetic adjudicator construction only.

- Candidate command was run once in Docker Desktop using the frozen image digest, network disabled, read-only container root, one CPU and 256 MiB memory; exit 0.
- Independent raw-only auditor command was run once in the same frozen container; exit 0.
- All 729 paired sign vectors matched the independent oracle; 0 mismatches.
- All 12 frozen controls matched, including malformed model identity returning `identity_format:model_contract_sha256` before cross-session equality and valid-but-different identity returning `identity_mismatch:source_bundle_sha256`.
- All four audit mutation probes were rejected (omitted case, forged tie PASS, duplicate case, mutated control).
- Raw candidate artifact: `results/construction-01/RAW.json`, 212,964 bytes, SHA-256 `472ccc001124df14095fa5486b6376b668e61b544a9e69b74befced4c3cc3b5c`.
- Audit artifact: `results/construction-01/AUDIT.json`; run receipt: `results/construction-01/RUN.json`.

Docker image: `python@sha256:afc139a0a640942491ec481ad8dda10f2c5b753f5c969393b12480155fe15a63` (`linux/amd64`, CPython 3.12.3). This is a construction-level code/oracle agreement result only. It does not establish empirical measure validity, live MAP01 outcomes, runtime/input safety, or authorization for #59/#5085. It does not amend or replace the immutable v1 `FAIL_AUDIT`.
