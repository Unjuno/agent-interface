# Docker Unix-socket Xvfb queue recheck R02b

## Outcome

`PASS_SCOPED_XVFB_QUEUE_RECHECK`. One normal and one optimized (`python3 -O`) run passed the exact XRes held-key disconnect discriminator on an isolated Docker Xvfb using its private Unix socket. Both runs observed the initial held `a`, confirmed the XTEST owner disconnected by XRes, observed `a` still down immediately after disconnect, observed an independent release transition, and read both `a` and `b` up at the 8.5 s post-termination horizon. Neither run observed the delayed synthetic `b` KeyPress. Final cleanup independently reported both keys up.

Both runs used Xvfb `2:21.1.7-3+deb12u13`, server release 12101007, XRes 1.2, XTEST 2.2, and server SHA-256 `6eda36f0c84969a0fbe3f411c4a16521620db8a16c13defbee690cad86bd9ef8`. Each unittest ran 1 test in about 8.6 s and exited 0. Full JSON, stdout, test log and Xvfb log for both attempts are preserved under `runs/`.

## Reproduction and custody

Conditions and source blob hashes are frozen in `conditions.json` and `source-blobs.txt`. The exact two source files match both the pinned source revision and the local checkout. The healthy existing image was used ephemerally with `--network none`, a read-only root filesystem, private tmpfs, and only this packet mounted writable. No shared WSLg socket, host display, provider, Relay, target GUI, or physical input was used. `audit_packet.py` verifies source pins, both attempt predicates, the queue discriminator, cleanup and all 18 checksummed evidence files. Audit output and exit code are retained.

## Limits / next gate

This is synthetic XTEST/Xvfb evidence on one container image and one bounded pair. It establishes the selected delayed-key queue outcome and release transition for this fixture. It does not prove production native-owner recovery, standard MCP caller composition, task effect or success, reliability, matched token/latency/correctness, live MAP01, or Research Preview acceptance. Next, exercise the standard caller's generation-bound operation through a finite synthetic disconnect/recovery composition with an independent effect receipt; then resume live MAP01/efficiency only under their existing allocation and custody gates.
