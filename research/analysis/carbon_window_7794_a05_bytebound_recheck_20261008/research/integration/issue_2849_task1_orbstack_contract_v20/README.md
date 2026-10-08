# Issue #2849 selected-backend OrbStack contract gate v20

This is a no-task, no-model-call successor. It inspects the exact selected Docker backend command builder from current main, checks the command's mount and socket/context contract, and independently validates the host broker's `/repo` path translation. It must not start a task runtime or host model broker.

The gate uses an isolated temporary directory and `docker --context orbstack info`; it does not create, stop, or modify containers. Results are written to the seed evidence directory and checksummed.

This gate is construction evidence only. It does not establish task completion, model quality, live IPC success, six-task acceptance, or efficiency.
