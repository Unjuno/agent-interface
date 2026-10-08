# Cross-agent Docker context reconciliation

At 2026-09-28 01:41 UTC another task reported a running
`cans-hg-n128-dt0.001` container on its `orbstack` context with image
`sha256:dd2b2eb63b12896a9b6e7a46563ed96b26d1c78c3e3749536d40d456895f722b`.
That image differs from this allocation's pinned Python image. The reporting
task later corrected its note (#5085 comment 5861828065): its local contexts
were `default` and `orbstack`, with no `desktop-linux`; it concluded the
observed container belonged to a different daemon and was not evidence of a
competing #5133 run.

This task's read-only check on the assigned host returned context
`desktop-linux`, no running containers, the exact pinned Python image ID, and
`docker inspect cans-hg-n128-dt0.001` returned `no such object`. No context
switch and no container mutation occurred. The completed #5133 formal and
audit remain attributed only to their frozen `desktop-linux` commands and
their durable raw/audit receipts. No other task's container is included in
this allocation.
