# Issue #2849 formal task-1 OrbStack run v24

One fresh seed 284924 allocation: task-1/layout-A/cold/plain. The main v2 task runtime runs in the pinned outer OrbStack image. Its selected Docker backend starts at most one pinned nested model container over the mounted OrbStack socket; a host-local broker permits at most one identified Codex CLI image call. No retry. Existing runtime observation, action admission, exact fixture submission, and verified release gates remain authoritative. This is not six-task acceptance or an efficiency claim.
