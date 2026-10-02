# A06 run record — `STOP_OUTPUT_PERMISSIONS`

**Disposition:** `STOP_OUTPUT_PERMISSIONS`; candidate invocations R=1 and Python=1, both exit 1; independent auditor=0 (not invoked); retries=0. No likelihood fit result was produced.

The six new frozen synthetic samples were generated in the pinned R 4.4.3/ismev 1.43 OrbStack container before freeze. Candidate source parsing, package/version checks, read-only input mounts, network isolation, and the configured 1 CPU / 2 GiB / 0-swap envelope passed preflight. Both candidate containers were created with read-only root, network `none`, read-only source/input binds, distinct output binds, `--cpus=1 --memory=2g --memory-swap=2g`, and user `1000:1000`; `docker inspect` confirmed these settings before either start.

Both one-shot candidates failed before producing JSON because the OrbStack VM bind-mounted output directories were owned by host-mapped UID/GID 501, while container UID/GID 1000 lacked write permission:

- R stderr: `cannot open file '/output/r.raw.json': Permission denied`.
- Python stderr: `PermissionError: [Errno 13] Permission denied: '/output/python.raw.json'`.
- Both exit files contain `1`; stdout files are empty.

Because both candidate arms did not exit 0, the frozen protocol required no auditor invocation; auditor count is 0. The experiment yields no evidence about optimizer sensitivity or Python/R numerical parity. The output-mount UID mismatch is an infrastructure/protocol failure, not a scientific negative result. No chmod/chown, candidate repair, candidate rerun, auditor invocation, or reuse of A06 seeds is permitted. A future attempt requires a distinct successor allocation with fresh seeds and an output-ownership design that is validated before freezing/candidate start.

The VM was dedicated to #6576 and used its private Docker Engine; no shared OrbStack Engine or other experiment VM was used. The private daemon's unrelated task-owned image-preparation container had been inspected as idle and stopped before this run; it was retained, not removed. All candidate source, preregistration, inputs, stdout/stderr, exit codes and hashes are retained with this package. A06 is not the formal six-case T0 and does not alter the A05 result.
