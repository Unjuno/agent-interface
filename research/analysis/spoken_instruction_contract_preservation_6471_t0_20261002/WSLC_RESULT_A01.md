# Issue #6471 T0 — second-host WSLc execution record

## Disposition

`PASS_METHOD_SCOPED` for the frozen authored-text method gate only. This does not establish the Issue's broader H about speech recognition or human intent, and does not test audio, ASR, prosody, a model, GUI effects, authority, safety, or deployment.

The original `FREEZE.json`, `RUN.md` HOLD, Issue comment, and PR #6494 remain unchanged. At the original freeze, formal candidate/auditor counts were both zero because the macOS host lacked WSLc. This record resumes that still-unconsumed candidate/auditor sequence on a Windows host with Microsoft's native WSL Containers CLI.

## Frozen input and current-main relation

- Allocation: `SPOKEN-CONTRACT-PRESERVATION-6471-T0-20261002-01`.
- Frozen base: `67ebd3016af9ed99a5cb40a39d4d753871f51d75`.
- At execution intake, the PR branch was based on current `main` `b6c16aa4e505f6bc2c206bf9d078e3042be91ce9`; the frozen base was an ancestor of that main. The exact package bytes below matched `FREEZE.json` after LF normalization.
- `candidate.py`: `a625f38c67154feb796d3ae7fe9f82cb1fc1078fb62508928359032fd8667229`.
- `audit.py`: `99e34da99fad056c408b172102976de0540f8c5aff81ad2e07caa0b5f4265be9`.
- `cases.json`: `ce9627502c437584aebea16b29763c052903af8e6a74b12749d025bbf1a8c516`.
- The WSLc execution copies of `candidate.py`, `audit.py`, and `cases.json` were checked against these hashes before their respective run. Frozen source files were not edited.

## Runtime and invocations

- Windows 10.0.26200.9457; Microsoft WSL/WSLc `3.0.1.0`; WSL kernel `6.18.40.1-1`; Linux/amd64.
- Image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; inspected image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`; CPython `3.12.14` per image configuration.
- Both started containers used `--pull never --network none --cpus 0.25 --memory 512m --user 65534:65534`; no GPU was passed. The memory argument is requested configuration only: WSLc printed `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` for each run. No swap-limit or hard memory-enforcement claim is made.
- One preliminary OCI start attempt failed before Python process creation because WSLc could not create the candidate output-file mountpoint under the read-only source bind (`E_FAIL`, exit 1). Candidate raw remained empty; this is recorded as one pre-process launch failure, not a candidate process invocation. Its tool output was observed but the first temporary stderr log was overwritten by the subsequent successful run; `PRESTART_MOUNT_FAILURE.md` preserves the exact observed error and this logging limitation.
- Candidate entrypoint: one process invocation, exit 0. It evaluated all seven frozen cases. The candidate wrote `candidate.raw.json` to a separate writable execution copy whose code/input hashes matched the read-only frozen source before execution. Candidate stdout, stderr and raw are retained in `formal_wslc_20261002/`.
- Auditor entrypoint: one separate WSLc container and process invocation, exit 0, after candidate exit 0. It consumed a copied, hash-verified candidate raw plus frozen `audit.py` and `cases.json`; it did not import candidate code. Auditor stdout, stderr and `audit.raw.json` are retained.
- Candidate invocations: 1; auditor invocations: 1; candidate-process retries: 0; auditor retries: 0. WSLc start attempts: one pre-process mount failure plus the two successful container starts. Containers were launched with `--rm`; ephemeral container IDs were not captured.

## Result and independent reconstruction

- Seven of seven cases assigned exactly once; all expected dispositions and source/transcript spans reconstructed.
- 25 source/transcript span links checked.
- The benign filler deletion and wrong-recipient substitution had equal WER, both `0.1111111111111111` under the frozen tokenization.
- All four independent mutation controls rejected: transcript recipient label, source negation label, speech-act label, and source-span text.
- Independent auditor: `PASS_METHOD_SCOPED`, errors `[]`.
- Candidate raw SHA-256: `f33e61f71261c02560da59e7e5b74bdbd1efc61a5f4a536a940dd5dd6c0f2e04`.
- Audit raw SHA-256: `01e2ae65e355c22d50de644b2251e8d7377a626405046e163a5b80da8cd75cce`.
- All retained artifact hashes are in `SHA256SUMS_WSLc_A01`.

## Interpretation / limits

The finite T0 representation test passes: under these authored labels, equal WER did not distinguish benign filler loss from a recipient substitution, while the critical-slot gate blocked the changed recipient and rejected the seeded label/span mutations. This is a method result on a deliberately small synthetic corpus. It does not validate the authored labels against real user intent, demonstrate ASR error detection, compare clarification burden, establish a voice route, or support the broader H/T1. Issue #6471 remains open.
