# A02 execution record

Allocation: `issue7505-mode-flap-t0-a02-20261004`

Base: `2fbfc00f8e38f33d7d74fb7cc734fbf5b0a11ab0`
Runtime: WSLc 3.0.1.0, Linux/amd64, cached Python 3.12 slim image `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364` (`python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`). No pull; network disabled; source mount read-only; separate output mount; configured 1 CPU and 256 MiB; `/tmp` tmpfs 16 MiB. WSLc warned: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` No claim of effective resource isolation is made. The WSLc command lacks `--read-only` and `--pids-limit`; container IDs were not captured.

## Candidate — one invocation

Start/end and exact argument array: `formal_a02/candidate.start.json`, `candidate.end.json`. Combined stdout/stderr: `candidate.stdout.txt`. Exit code: `candidate.exit.txt` (0). Candidate wrote `raw.json`, 288 episodes and 23,040 event rows. SHA-256 and byte size are in `SHA256SUMS` and `MANIFEST.json`.

## Frozen auditor v1 — one invocation

Start/end and exact argument array: `formal_a02/audit.start.json`, `audit.end.json`. Combined stdout/stderr: `audit.stdout.txt`. Exit code: `audit.exit.txt` (1). It detected the missing per-episode alarm entries and raised `KeyError: 'rolling_mode_transition_count'`; no `audit.json` was written. This first outcome is retained and was not rerun.

## Supplemental raw auditor v2 — one post-run invocation

This read-only audit is explicitly postformal and uses the separately versioned `audit_v2.py` (hash in `MANIFEST.json`). It reads the unchanged `raw.json`, independently reconstructs alarms from scores, checks all source/state/metric/threshold/endpoint values, and runs the frozen corruption controls against a normalized in-memory copy. Exact invocation and raw hash: `formal_a02/audit_v2.start.json`; combined output: `audit_v2.stdout.txt`; exit 0: `audit_v2.exit.txt`; structured result: `audit_v2.json`. This does not rerun the candidate or erase auditor v1's failure.

## A01 launch STOP

A01's pre-container WSLc path failure is retained separately in `../mode_flap_7505_t0_a01_20261004/STOP.md` and its `formal_a01/` receipts. No A01 candidate output exists; A01 was not retried.
