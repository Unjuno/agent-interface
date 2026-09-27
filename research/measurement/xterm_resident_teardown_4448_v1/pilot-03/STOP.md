# Pilot 03 — diagnostic child-start stop

- Allocation: `issue4448-construction-pilot-03` (no formal allocation/seed).
- Source `pilot.py` SHA-256: `a312d33bce69cbb51cc1bcf72083f5603f56b98db19860c0c9584619f75397a3`.
- Image: `agent-interface-r3-batches:20260927-03`, `linux/arm64`.
- Container: `--network none --read-only`; bounded `/tmp` tmpfs; source read-only and output separately mounted.
- Diagnostic outcome: timeout waiting for `ready-0`; `xterm_poll=None`, `/proc` children field empty, `child_error=none`; effect rows/actions: 0.
- Retained exact terminal classification from the tool invocation: `TimeoutError: child readiness receipt missing: ready-0; xterm_poll=None; child_pids=; child_error=none`.
- Xvfb/Openbox/XTerm logs and launch argv are in `../pilot-03/run01/`.
- Classification: `STOP_PREFORMAL_XTERM_CHILD_NOT_OBSERVED`; scientific disposition: none.

The attempt is preserved and not pooled with pilot-04. No formal seed was consumed.
