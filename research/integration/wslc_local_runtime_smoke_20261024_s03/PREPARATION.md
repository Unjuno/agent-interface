# S03 preparation

Registered before session creation, image pull, or container execution. Source `64543a8ac5b01ac8acff3910e4fc2e0458276f6c`; unique session `agent-interface-wslc-s03-ae04b8be36f14cc3b7dd3cfd82f76092`; pinned image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.

The attempt-owned storage directory already exists. The session is started once with `wslc system session enter --name` and remains open while all session-scoped commands run. One exact image pull and one container execution are allowed. The container has `--network none`, requested 512M memory and 1 CPU, a read-only bind mount, `--rm`, unique name and CID receipt. It reads a fixed sentinel and requires an attempted write to fail with EROFS.

Any timeout or ambiguous receipt ends S03 as HOLD/UNKNOWN without retry. Cleanup is limited to exact CID and the dedicated session/image. This smoke cannot establish real Windows GUI computer control, input release, recovery, or task effect.
