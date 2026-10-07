# A02 run record

- Allocation: `5309-IDENT-A02-HOSTCPU-20261007`
- Frozen main: `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`
- Runtime: Python 3.14.5, host CPU, Python standard library only.
- Formal candidate: `python3 candidate.py > candidate-raw.json 2> candidate.stderr.txt` — one invocation, exit 0, stderr empty.
- Formal auditor: `python3 auditor.py candidate-raw.json > audit.json 2> auditor.stderr.txt` — one invocation, exit 0, stderr empty.
- Formal retries: zero. Do not rerun either formal command under this allocation.
- Candidate raw SHA-256: `38dac3760d04b741e491c9e49412ec9778f976b20967edcfa2b53c2c7073d9e1`.
- Audit SHA-256: `283008bb2f0b0968418974805e26a3ae01967330daaeaf1c8c6b3d8e23dc8b76`.
- Disposition: `PASS_METHOD_SCOPED`, limited to the authored finite model; see `REPORT.md` and `audit.json`.
- Container status: no container was run. OrbStack's Docker inventory was unavailable due a containerd blob `operation not supported`; Issue #5309 permits a deterministic no-container first rung. Host execution did not provide OS-level network isolation; scripts made no network calls.
- Construction controls passed before freeze. Post-freeze checks are limited to saved-evidence validation, syntax compilation, hashes, and repository CI; they must not invoke the candidate or auditor again.

The A01 predecessor remains unchanged and retains its own invalid-audit disposition. A02 is a separately frozen successor; its result must not be generalized to UI, live authority, model behavior, task utility, or product safety.
