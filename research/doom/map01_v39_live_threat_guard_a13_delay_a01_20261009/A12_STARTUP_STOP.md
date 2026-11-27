# A12 startup STOP

A12's one-shot launcher exited with guest status 2 before any model turn or game episode because its configured guest entrypoint path omitted the package's `_delay_a01` suffix. The exact A12 output and freeze are preserved privately. The allocation was not retried. A13 used a distinct sequential seed and added guest-side SHA-256 checks for the entrypoint and fixture before starting the app-server or game.
