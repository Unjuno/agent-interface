# Pre-run custody

- Intake and source commit: main `2d227ecf86479cff093123190560bd8d63148ce4`.
- GitHub question: Issue #8300, successor to #7949; prior allocations remain untouched.
- Allocation: `GUI-REVERSIBILITY-7949-JOURNAL-A01-20261007`.
- Runtime gate: `docker info` succeeded on OrbStack Engine 29.4.0 / CLI 29.5.2, linux/aarch64, kernel `7.0.5-orbstack-00330-ge3df4e19b0a0-dirty`; read-only `docker image ls --no-trunc` failed because an existing containerd content blob returned `operation not supported`. Docker listed 100 stopped containers and zero running containers. No container was started/stopped/removed and no image was pulled/built; no VM repair/prune/restart was attempted.
- Fallback: preregistered non-privileged native macOS Python standard-library process run. No container-isolation claim.
- Construction: `python3 construction_test.py` passed baseline, disjoint proposal, four fail-closed anomaly cases, cardinality controls and Python syntax. `python3 -m py_compile` passed for all seven Python sources. These were pre-freeze construction checks; no formal DBs were created and no formal stage CLI was invoked.
- Formal stages at freeze time: writer=0, observer=0, candidate=0, auditor=0; retries=0.
- One-shot conditions: `out/` must not exist at launch; writer/observer failure is terminal STOP; candidate/auditor each invoked once only after the prior stage exits 0; no retry, replacement, seed reuse or post-outcome source/gate edit.

See `FREEZE_SHA256SUMS.txt` for exact frozen input/source hashes. The freeze commit is the commit that records this file and its manifest; its SHA and verified run receipts are recorded in `RUN_RECORD.md` after formal execution.
