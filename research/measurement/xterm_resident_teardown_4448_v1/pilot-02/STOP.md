# Pilot 02 — pre-effect child-ready stop

- Allocation: `issue4448-construction-pilot-02` (no formal allocation/seed).
- Source `pilot.py` SHA-256: `845c76ddc9e0ae12a4f0b7be511db51d94d1bf42f0f695808e64455319bcd4d8`.
- Image: `agent-interface-r3-batches:20260927-03`, `linux/arm64`.
- Container: `--network none --read-only`; bounded `/tmp` tmpfs; source read-only and output separately mounted.
- Change from pilot-01: redirected HOME and XDG cache directories to `/tmp`; added per-XTerm log capture.
- First outcome: still timed out waiting for child `ready-0`; no effect rows/actions were emitted. XTerm process log was empty; Xvfb/Openbox logs are in `../pilot-02/run01/`.
- Retained setup stdout/stderr from the tool invocation: `TimeoutError: child readiness receipt missing: ready-0`.
- A separate diagnostic command then launched the same Python child under Xvfb **without Openbox**; it created `run01/probe.ready` and blocked waiting for Return. It emitted no effect and is not an arm or a paired observation. This diagnostic isolated the missing readiness to the WM-composed setup, but does not identify the cause.
- Classification: `STOP_PREFORMAL_CHILD_READY`; scientific disposition: none.

The attempt is preserved and not pooled with pilot-04. No formal seed was consumed.
