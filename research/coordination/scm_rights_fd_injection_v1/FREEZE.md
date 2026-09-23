# SCM_RIGHTS post-start descriptor injection v1 — source-first freeze

Task: COORD-SCM-RIGHTS-FD-INJECTION-20260917-022
Issue: #556
Publication BASE: 888399b4262dd6e459646cb28cff8f4f8602a25b
Scope: research/coordination/scm_rights_fd_injection_v1/**

Formal A1 is exactly plan.json: 12 fresh first outcomes, six 2-case chunks. Single factor is descriptor broker response after task start: control sends no descriptor; inject_fd sends the authoritative SQLite DB fd via SCM_RIGHTS. Both arms start UID/GID65534 with no authoritative DB fd, pathname DB access denied, same owner socket, same task source and same atomic check+commit. No retry, token refresh, permission change, broker-policy change, alternate dependency or post-result tuning.
