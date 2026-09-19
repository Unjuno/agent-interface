# SO_PEERCRED SCM_RIGHTS broker gate v1 — source-first freeze

Task: COORD-SCM-PEERCRED-GATE-20260917-023
Issue: #580
Publication BASE: ad93a12348df9539957a3e54f20775991118ef5a
Scope: research/coordination/scm_peercred_gate_v1/**

Formal A1 is exactly plan.json: 12 fresh first outcomes, six independent 2-case chunks from the start. Single factor is descriptor-broker admission policy: unguarded sends the authoritative DB fd; peer_guard reads kernel SO_PEERCRED and only sends an fd to peer uid 0. Both experimental tasks are UID/GID65534, start with no authoritative DB fd, retain pathname denial, same world-writable broker socket, same task/owner semantics and same atomic check+commit. No retry, token refresh, socket-mode change, peer-policy change, alternate dependency or post-result tuning.
