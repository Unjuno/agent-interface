# Execution and local validation log — Issue #5006

- Container: OrbStack context; pinned image digest, observed linux/arm64; Python 3.12.14.
- Invocation: `issue5006-audit-typehash-20260928-01`, one run, exit 0; no retry.
- Network: none. Root filesystem: read-only. Source and input mounts: read-only.
- Resource caps: 1 CPU, 512 MiB memory, 32 PIDs.
- Raw stdout: retained verbatim in `RESULT.md`; generated output files retained under `output/`.
- Local post-run CI: PASS — syntax-compiled 3 Python files without writing bytecode; checked retained summary reports 336 rows / 21 distributions, all 6 bool cases have recorded legacy acceptance and strict-type rejection, and all 3 manifest negative controls reject.
- Full repository GitHub Actions checks are not represented as local CI; this working directory is not a Git checkout. PR checks are the authoritative repository CI gate.
- Allocation disposition: `HOLD_PROVENANCE_OR_RUNTIME`. The exact platform was not met and the executed new sources were not publicly frozen/read back before invocation. This is an explicit STOP/HOLD record, not a formal PASS.

Reproduction sources and artifact hashes are recorded alongside the raw bundle. Do not rerun this consumed allocation.

