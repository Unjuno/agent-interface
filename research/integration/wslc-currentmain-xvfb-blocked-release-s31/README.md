# S31 current-main WSLc private-Xvfb replicate

S31 uses a fresh unique WSLc session on the user's authorized Windows PC to repeat the same 3,935 ms current-main standard-caller private-Xvfb condition as S29. S30 stopped before any container/task input because its first session-scoped exact-name preflight returned `ERROR_PATH_NOT_FOUND`. S31 changes only session-readiness handling: it polls the exact generated container name within the newly created session for at most 10 seconds, and starts the test body once only after an empty successful response.

The runtime, staged assets, source and bounds are held constant. The existing S30 input audit verified all five source/dependency/stage/XKB/runner manifests exactly against the passed S29 audit. The assets are reused read-only. S31 does not inspect global WSLc state and does not use Docker.

The scope is one synthetic private-Xvfb observation. It cannot establish physical Windows input, MAP01 or live application control, reliability, a stable timing threshold, model/provider economics, or clearance of unrelated shared WSLc ownership.
