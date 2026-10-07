# Frozen run protocol

Runtime: native macOS Python standard library only; no venv, package installation, network, GUI, host input, privilege, Docker repair, image pull/build, or actual compensation. Python executable is resolved as `python3` on this host and its full version/path are recorded in `RUN_RECORD.md`. This is not container-isolated.

Run from this directory after the freeze commit, with `out/` absent:

1. `python3 run_all.py` — create six fresh SQLite databases, invoke one writer and one read-only observer subprocess per case, and retain DBs, observer snapshots, per-process stdout/stderr/exit receipts and database hashes. A failure is STOP; do not retry.
2. `python3 invoke_stage.py candidate` — invokes candidate subprocess exactly once and records exact stdout/stderr bytes and exit. Nonzero is terminal; do not retry.
3. `python3 invoke_stage.py auditor` — invokes independent auditor subprocess exactly once against retained DBs/observations/candidate output and records exact stdout/stderr bytes and exit. Nonzero is terminal; do not retry.

The steps are sequential. Do not run construction tests after freeze or after any formal invocation. The only pre-freeze construction command is `python3 construction_test.py`; it calls in-memory decision functions on authored fixtures but does not create formal DBs or invoke the formal stage CLIs. After construction passes, freeze all sources and inputs in `FREEZE_SHA256SUMS.txt`, commit that freeze, verify hashes, and only then start step 1.
