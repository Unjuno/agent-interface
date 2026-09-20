# Allocation formal-01 — STOP before container creation

Allocation `issue3188-source-bound-entry-gate-formal-01` did not execute candidate source and produced no `raw.json`.

- Frozen image existed and `docker image inspect` resolved ID `sha256:2f17fc044b579bab302c2e8053d4a686e2cb9a83de48e70534b94cd8ebbe06a9` as Linux/arm64.
- The frozen command used that image ID as the `docker run` image reference. OrbStack Docker Engine 29.4.0 rejected it with `No such image`; no container was created.
- Captured CLI output is `container.log`; its SHA-256 is recorded in `SHA256SUMS`.
- This is a runtime invocation/setup STOP, not a candidate, gate, or scientific failure. No same-allocation retry is permitted.
- A separately identified successor allocation may use the already verified immutable `python:3.12-slim` local tag, but must reverify that the tag resolves to the exact same image ID before one invocation.
