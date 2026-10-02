# Allocation 01 — `PASS_METHOD_SCOPED`

## Outcome

Frozen candidate emitted 9 rows (exit 0). A separate independent auditor reconstructed every row and the hidden truth table with zero errors (exit 0). It counted one eligible teaching step and four true task-effect claims; the other verified-effect claims included a missing-release case, an irreversible case, and an opted-out case, all of which were correctly excluded from teaching. False-success, uncertain, wrong-target, stale-generation and ambiguous-target cases were not presented as demonstrated. Skip and stop remained available in all rows and action authority remained false.

Scope is strictly finite method validation on authored JSON cases. It does not validate participants, GUI effects, actual application receipts, learning/retention, safety in a live interface, time or user benefit.

## Provenance

- Allocation/source commit: `FADED-DEMONSTRATION-6600-T0-ORBSTACK-20261002-01` / `0ddd8def9d7b65fe16c78273d5ae60959acec9d8`.
- Base main: `aa0311f4501be749c117cbc3c73e5bd3f13bf744`.
- Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Candidate container `ae39bfcc3fb7594a8b2ce4d21c7aeb1a965f020b0fb65edcbbe26bcaa15dc20e`; auditor container `10f74a60bdf14994f9cf52af6291fb66bbe5b92e9039000a3dcad5efb037e24c`; each exit 0, network none, read-only rootfs.
- Candidate mounted only `candidate.py` and public fixture read-only. Auditor mounted source/oracle and raw read-only; separate audit output was writable. Only these two new containers were removed after inspect/log capture; pre-existing containers were untouched.
- Candidate raw SHA-256 `209ab5cebc124fc9a5617d338b62ac66e420aa1f52214d211c033d9720b35ec1`; audit SHA-256 `14e85b3bad71326d458d3a30684a3bd1eca81364a236e3d0ad12568c0b0f829e`.
- Fixture SHA-256 `5550d8ef77976d5b538524c61b1487500e0cedad4fbda89745027c1a827257b1`; hidden oracle SHA-256 `a12bd0ef4a307b6674c3e60a4b4606b8a0eec05b36dc94a26b98d8017e9338c1`.
- Candidate source SHA-256 `73166c78fa223dd73431f1fa676f07042baab3799f14e63e5665523984078137`; auditor source SHA-256 `8d5570bb615a38566cc7c690536b225c18206bcd3806a96bdcf85153c489312f`.
- Construction=5/5; candidate=1; auditor=1; retries=0.

## Exact commands used

Candidate: `docker run --name faded6600-candidate-20261002-01 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --mount type=bind,src=/Users/taka/Documents/Codex/2026-10-02/agent-interface-6600-t0-orbstack/research/analysis/faded_demonstration_6600_t0_orbstack_20261002/candidate.py,dst=/candidate.py,readonly --mount type=bind,src=/Users/taka/Documents/Codex/2026-10-02/agent-interface-6600-t0-orbstack/research/analysis/faded_demonstration_6600_t0_orbstack_20261002/fixtures.json,dst=/fixtures.json,readonly --mount type=bind,src=/tmp/faded-demo-6600-t0-20261002/candidate,dst=/out python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /candidate.py /fixtures.json /out/candidate.json`.

Auditor: `docker run --name faded6600-auditor-20261002-01 --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --mount type=bind,src=/Users/taka/Documents/Codex/2026-10-02/agent-interface-6600-t0-orbstack/research/analysis/faded_demonstration_6600_t0_orbstack_20261002,dst=/src,readonly --mount type=bind,src=/tmp/faded-demo-6600-t0-20261002/candidate,dst=/raw,readonly --mount type=bind,src=/tmp/faded-demo-6600-t0-20261002/audit,dst=/out python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f python -B /src/auditor.py /src/fixtures.json /src/oracle.json /raw/candidate.json /out/audit.json`.
