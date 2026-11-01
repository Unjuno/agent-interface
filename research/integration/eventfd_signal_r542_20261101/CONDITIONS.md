# One-shot eventfd probe r542

Before running, compare three fixed-order arms using a fresh Linux eventfd and a
spawned child per arm: unrevoked control (child poll should not see readability),
parent writes once before child polls (child should see readability), and child
is killed after attaching the descriptor but before the parent's one write
(write should return and child exit should be observed). Missing observations,
incorrect child exit, I/O errors or failed cleanup are not passes. Each arm has
one sample; record syscall elapsed time without claiming a hard time bound.

Use Python 3.11 in the pre-existing pinned Docker image
`sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`,
`--network none --cpus 1 --memory 1g --pull never`; mount this script read-only.
The eventfd is nonblocking and close-on-exec, passed by multiprocessing DupFd;
the child polls but never drains it. No display, network, real user input, actual
MCP operation or cancellation is involved. The process is always joined, with a
kill fallback on abnormal exit. This tests the narrowly controlled notification
mechanism; it does not fence an action already past the child check, prove X
queue drainage, protect against all process/descriptor failure races, or prove
bounded system calls. Retain the full JSON, script, and runtime identification.
