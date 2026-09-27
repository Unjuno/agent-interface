# SO_PEERCRED broker gate — retained result

Decision: **PASS_SO_PEERCRED_GATE_SCOPED**.

The broker socket remains mode 0666 in both arms and task UID/GID is 65534. The single factor is broker admission policy.

- unguarded/stable: 3/3 broker sends DB fd via SCM_RIGHTS; A-only token; generation2 commits.
- unguarded/B_change: 3/3 old B is read without receipt, B changes rev1→rev2, stale generation2 commits.
- peer_guard/stable: 3/3 SO_PEERCRED records uid/gid65534, fd transfer denied, task falls back to owner socket and A/B token; generation2 commits.
- peer_guard/B_change: 3/3 fd transfer denied, A/B token detects B revision mismatch; generation remains1 and no generation event.

Formal measured-ID reruns: 0. Frozen audit errors: 0. Copied-evidence corruption controls rejected: 4/4.

Interpretation: a kernel peer-credential gate can close this specific world-writable SCM_RIGHTS descriptor-transfer path without removing the socket itself. Correctness still depends on the trusted-UID policy and on there being no other authoritative descriptor-transfer path.

Limits: one Linux/Python/SQLite fixture. No general sandbox/security proof, user-namespace identity analysis, cryptographic identity, pidfd/procfs transfer, privileged-task threat model, distributed concurrency, crash/power-loss, or performance claim.
