# Event lock fault injection r540

Question: in this pinned Linux/CPython environment, can killing a process while
it holds the internal lock used by `multiprocessing.Event` prevent another
process from returning from `set()`? This probes a specific possible failure of
the Event-based draft; it does not claim the real owner is killed at that point.

Before execution: one fixed-order released-lock positive control followed by
one killed-lock-owner arm. The child deliberately holds the CPython private
`Event._cond._lock`; in the first arm it releases and exits normally, in the
second it is killed while holding. Only after the holder is observed exited does
a separate setter call `Event.set()`. The controller observes the setter for
one second, then kills and joins it if still alive. The result is the two process
exit/liveness observations and any returned receipt, not a hard real-time bound.
Both children are forcibly cleaned up in the harness. Missing readiness or failed
cleanup is an error, not a pass. There are no user GUI or physical inputs.

Environment: Docker isolated `--network none --cpus 1 --memory 1g --pull never`,
image sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425,
Linux CPython, fork start method. Python/platform versions are emitted. One
sample per arm; scope excludes other platforms, implementations and voluntary
normal process exit. The raw JSON and original script must be preserved.
