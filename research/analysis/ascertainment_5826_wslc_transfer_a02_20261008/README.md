# Issue #5826 A02 — WSLc container-transfer replication

**Disposition: `PASS_WSLc_TRANSFER_SCOPED`, with the legacy auditor scope-label mismatch preserved.** The frozen A01 candidate and independent oracle auditor both ran in isolated WSLc containers using the cached pinned Python image. The candidate recreated the 18-opportunity / 72-channel-row fixture, the independent calculations matched A01, and all five saved-data corruption controls were rejected. This is a new runtime-transfer result; it does not modify or pool A01 host evidence.

The candidate output identifies Linux x86_64 / Python 3.12.14 under the WSL2 kernel. The auditor returned exit 0 and the expected reconstruction, but its unchanged A01 source prints the stale strings `PASS_METHOD_SCOPED_HOST` and `HOLD_CONTAINER_TRANSFER (not exercised)`. Those labels are hard-coded unconditionally after the audit calculation; they do not inspect execution environment. Preserve them verbatim and use the separate WSLc command/image/mount record for runtime scope. No source was patched to conceal the mismatch.

See [report](REPORT.md), [freeze and exact commands](PREREGISTRATION.md), [execution output](EXECUTION.txt), raw candidate/auditor/mutation artifacts in `out/`, and byte-identical source copies in `source/`.

Limits: one deterministic synthetic CPU workload and one WSLc host/image combination. The WSLc startup warned that swap limits or cgroups are unavailable; `--memory 256m` and `--cpus 0.25` are recorded as requested values, not verified enforcement. This is not Docker/OrbStack equivalence, live failure ascertainment, a hidden-incident estimate, a safety result, or product integration.
