# Pilot 01 — pre-effect setup stop

- Allocation: `issue4448-construction-pilot-01` (no formal allocation/seed).
- Source `pilot.py` SHA-256: `915c682e19724f2f093527207ed95a35b125aa136d34b483e85d07bd2d490b06`.
- Image: `agent-interface-r3-batches:20260927-03`, `linux/arm64`.
- Container: `--network none --read-only`; bounded `/tmp` tmpfs; source read-only and output separately mounted.
- First outcome: timeout waiting for XTerm child `ready-0`; no effect rows/actions were emitted.
- Retained setup stdout/stderr from the tool invocation: `TimeoutError: child readiness receipt missing: ready-0`.
- Xvfb/Openbox logs are in `../pilot-01/run01/`. They contain Openbox/fontconfig messages about unavailable writable root-home caches and the optional Debian menu file.
- Classification: `STOP_PREFORMAL_CHILD_READY`; scientific disposition: none.

The attempt is preserved and not pooled with pilot-04. No formal seed was consumed.
