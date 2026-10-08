# Same-UID SO_PEERCRED identity granularity — retained result

Decision: **PASS_PROCESS_IDENTITY_GATE_SCOPED**.

An authorized inert helper and the experimental task both run UID/GID65534 but have distinct PIDs. The broker socket remains mode0666.

- uid_only/stable: 3/3 same-UID task is authorized, receives DB fd, A-only token, generation2 commits.
- uid_only/B_change: 3/3 task PID differs from helper PID but UID-only policy still sends fd; old B=b1 is read without receipt, B becomes b2/rev2, stale generation2 commits.
- uid_pid/stable: 3/3 broker records same UID but task PID != helper PID, denies fd; owner-socket A/B token, generation2 commits.
- uid_pid/B_change: 3/3 fd denied, A/B token detects B revision mismatch; generation remains1 and no generation event.

Formal measured-ID reruns: 0. Frozen audit errors: 0. Copied-evidence corruption controls rejected: 4/4.

Interpretation: UID-level peer identity is too coarse when trusted and untrusted processes share a UID. Exact PID binding discriminates this fixture, but raw PID is not promoted as a durable security principal because PID reuse/lifecycle remain untested.
