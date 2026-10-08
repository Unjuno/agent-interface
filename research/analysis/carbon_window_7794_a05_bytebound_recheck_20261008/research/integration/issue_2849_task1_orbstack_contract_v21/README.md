# Issue #2849 OrbStack socket/workspace construction probe v21

Seed 284921 is a no-task, no-model-call construction probe preregistered in Issue #2849. It starts at most one pinned outer container with networking disabled and runs only `docker version` through the explicitly mounted OrbStack socket. Separately, it constructs (but never executes) the selected backend's exact Docker argv and checks its workspace mount against the host broker `/repo` mapping.

This is infrastructure/contract evidence only, not a task, model, six-task, efficiency, or reliability result.
