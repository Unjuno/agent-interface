# Xdummy native XKB map round-trip v1 — retained harness failure

Task `XKB-XDUMMY-MAP-ROUNDTRIP-20260916-001`, Issue #380. Source-first freeze HEAD `5c91eee6a4c3ac66614226df63d3e502f6071373`.

Decision: **`HARNESS_FAIL_AUTH_ENV`**. Do not interpret this allocation as evidence for or against Xdummy native XKB loading.

The formal allocation was consumed once. Three fresh Xdummy/Xorg servers on :180/:181/:182 all started successfully, exposed XKEYBOARD, and terminated normally. Each arm then failed before baseline keyboard-map measurement because the runner created the correct per-arm Xauthority and supplied it to subprocess commands through a private `env` mapping, but did not update the runner process's own `os.environ`. `python-xlib` therefore attempted its inherited `/opt/xvfb/.Xauthority` and raised `Xlib.error.XauthError`.

All three retained partial result records have `startup=true`, `xauth_returncode=0`, `xkeyboard_present=true`, `input_operations=0`, and no decision/result measurements beyond that point. `run_block.py` subsequently raised `KeyError('decision')`; this is downstream of the same missing typed harness terminal.

No formal rerun is allowed under this task ID. One excluded construction performed manually in a shell with `DISPLAY` and `XAUTHORITY` exported did show Xdummy can load the same resolved German XKB and change live server/core/modifier state, but that construction remains excluded and is not substituted for the failed formal allocation.

Successor rule: change only authentication-environment propagation and typed exception finalization; keep Xdummy invocation, German resolved SHA, XKB load/readback gates, displays, no-input contract and three-arm count unchanged under a new task identity.

Evidence archive `xkb_xdummy_map_roundtrip_v1_failed_evidence.tar.xz`: 26,828 bytes, SHA-256 `b9b6a28e321b3835d660ae8f75beecc2fee1d8cae668fa3c9a140967f34af63c`; manifest SHA-256 `39473da6b328937d710d5ec2c15d85b3219ebc2640a3b6422578fbd2d73d8d1b`; 41 files including manifest.
