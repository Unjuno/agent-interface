# Inherited authoritative DB fd bypass — retained result

Decision: **RETAIN_INHERITED_FD_BYPASS_BOUNDARY_SCOPED**.

The pathname capability boundary remains intact in both arms: task UID/GID is 65534, direct SQLite pathname access fails `OperationalError`, DB is root-owned mode 0600 inside root-owned mode 0700 directory. The single changed factor is whether the parent passes an already-open authoritative DB descriptor into the task.

- no_fd/stable: 3/3 socket-mediated A/B token, generation2 commit.
- no_fd/B_change: 3/3 token includes B and rejects B rev1->rev2; generation remains1, zero generation event.
- leaked_fd/stable: 3/3 pathname denied but inherited fd bytes deserialize to recover B, token contains A only, generation2 commit.
- leaked_fd/B_change: 3/3 old B=b1 was read through inherited fd without receipt, B becomes b2/rev2, A-only token remains current and stale generation2 commits.

Formal measured-ID reruns: 0. Frozen audit errors: 0. Copied-evidence corruption controls rejected: 4/4.

Interpretation: filesystem pathname isolation is not sufficient if effect-relevant authoritative descriptors leak across the process boundary. Mandatory mediation requires capability hygiene over inherited file descriptors as well as pathname permissions.

Limits: one Linux/Python/SQLite fixture; `sqlite3.deserialize()` is the concrete parser. No general sandbox/security proof, SCM_RIGHTS, seccomp/namespaces, privileged task, distributed system, crash/power-loss, performance or natural-rate claim.
