# S02 preparation

Registered before any pull or container run. Source commit: `64543a8ac5b01ac8acff3910e4fc2e0458276f6c`. Dedicated session: `agent-interface-wslc-s02-e8fb33d5af824e7eb4496edd27c5116d`. Pinned image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.

This experiment tests only a WSLc runtime's basic isolated execution and read-only bind mount. It is not evidence of GUI input, release, app reaction, bounded recovery, or task effect.

One pull and one run are allowed. The run requests `--network none`, `--memory 512M`, `--cpus 1`, `--rm`, a unique name, and an exact CID file. It reads the mounted sentinel, checks its bytes, attempts one write, and requires Linux `EROFS`. On any timeout or ambiguous receipt, stop with HOLD/UNKNOWN and preserve the run directory. No retries and no global inventory.

After a complete run only, query the exact CID. If absence is confirmed, remove only this session's exact image and terminate only this session. Preserve all stdout/stderr and command status.
