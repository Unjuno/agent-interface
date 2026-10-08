# Issue #6624 T0 run log — protocol STOP

- Allocation: `ARTIFACT-CHANGEABILITY-6624-T0-HOSTCPU-20261002-01`.
- Frozen base main: `d9e2448e6dd53e36a2ac9352c09e0bfd39f971f7`; frozen branch pre-candidate ref matched the same SHA. Post-run main check observed `840c70eb2815767ae6993d1373ab0596600b813d`; exact advance timing relative to candidate/auditor is unknown.
- Runtime: Windows host CPU, CPython 3.11.9, standard library only.
- Construction history: first suite run failed 6 tests because cost accounting lacked a `none` key; this occurred before candidate output. Fixed during construction. Final pre-run suite passed 6/6, including seven corruption controls.
- Immediate local pre-run gate: all nine frozen source/input hashes matched `FREEZE.json`; both output paths absent. GitHub main and branch refs were checked immediately before candidate and both equaled the frozen SHA.
- Candidate: `python run_candidate.py candidate_raw.json`, exit 0, created 11,909 bytes at `2026-10-02T08:52:53.8136726Z`; SHA-256 `3c19805b28a8345b226583472a68532e17f883a2c555a5b6c64b368725662f85`.
- Auditor: separate process `python run_audit.py candidate_raw.json audit.json`, exit 0, created 373 bytes at `2026-10-02T08:53:00.2897770Z`; audit output was `METHOD_PASS_SCOPED`, 12 rows, errors `[]`; SHA-256 `26a57fd1918b4a759b3403e868a9649ee4b43c6cfdb211dfe9b29c3b9afa22bb`.
- **Protocol reconciliation:** candidate and auditor ran from the source package directory, not an isolated copy as frozen README required. The Issue also required independent review before freeze; none was obtained. These are predeclared protocol requirements, so despite internally passing raw audit, the overall allocation is `STOP_PROTOCOL_DEVIATION`, not an accepted method PASS.
- Candidate/auditor/retries: 1/1/0. Do not repeat or amend this consumed allocation. Preserve raw output and stop record verbatim.
- Resource counts: model/GPU/CUDA/optimizer/adapter/Docker/WSLc/network/GUI/game/input = 0.
