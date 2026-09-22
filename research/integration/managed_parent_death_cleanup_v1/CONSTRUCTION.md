# Excluded construction chronology

Formal cases executed: 0/16.

1. Construction-01 exposed two harness defects before any formal use: the manager accepted `NORMAL_EXIT` while the frozen schedule called the event `MANAGER_NORMAL_EXIT`; and the construction auditor expected formal `batch*/case-*` layout. No scientific row was consumed.
2. Construction-02 fixed event mapping/auditor layout and exposed a real environment/evidence problem: this container's PID 1 did not immediately reap orphaned baseline workers/helpers, so rescue left zombies and the cleanup gate correctly failed.
3. Construction-03 made the case orchestrator a Linux child subreaper and made explicit cancel wait/reap its worker. Six excluded cases then passed the same semantic checks: candidate normal exit, SIGKILL, explicit cancel, client disconnect; baseline SIGKILL and client disconnect. Prefix audit: 6 cases, 45 checks, errors=[].

These are construction corrections only. Scientific policies, four event families, two repetitions, formal denominator 16, and decision gates are unchanged. Construction rows are excluded from formal evidence and will not be pooled.
