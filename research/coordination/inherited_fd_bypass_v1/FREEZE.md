# Inherited FD bypass v1 — source-first freeze

Task: COORD-INHERITED-FD-BYPASS-20260917-021
Issue: #542
Publication BASE: a8327e1b04b9ed82d903c57b3a957ee998705ab6
Scope: research/coordination/inherited_fd_bypass_v1/**

Formal allocation A1 is exactly plan.json: 12 fresh first outcomes, six 2-case chunks. Scientific factor is inherited authoritative DB fd only. Both arms run UID/GID 65534, pathname DB access must fail, same socket owner and same task source. No retries, token refresh, permission changes, alternate dependency path, or threshold changes after first outcome. Construction rows are excluded.
