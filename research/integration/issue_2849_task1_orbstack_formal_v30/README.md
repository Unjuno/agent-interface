# Issue #2849 formal task-1 finish-reconciliation successor v30

One fresh formal seed 284930, task-1/layout-A/cold/plain. This wrapper explicitly calls the fixture's finish operation before reconciling the returned task trace against the materialized exact submission history. The source pattern is independently exercised in Issue #3798 offline replay. Maximum one host Codex image-backed call, no retry; one pinned network-none outer and one pinned network-none nested OrbStack container. Six-task acceptance and efficiency remain out of scope.
