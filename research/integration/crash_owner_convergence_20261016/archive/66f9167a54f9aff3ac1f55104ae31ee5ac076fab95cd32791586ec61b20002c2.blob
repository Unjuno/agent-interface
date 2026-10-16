# A02 — setup STOP: shared X11 socket directory

**Disposition: `STOP_INFRA_X11_SOCKET_DIRECTORY`.** The one candidate invocation did not start a session child or owner service. Xvfb reported that `/tmp/.X11-unix` permissions did not permit creating its listener, then timed out waiting for `-displayfd`. The raw error record is preserved at `results/A01/RAW.json`; its SHA-256 and exact invocation are in `RUN.json`.

This is a setup outcome, not evidence about the process-owned backend hypothesis. The shared WSL socket directory was left unchanged. Preflight also found missing NumPy and openpyxl; NumPy was added only under `/tmp/v15-owner-a02-deps`, and the unused `gui_suite` import was stubbed for preflight. The next separately frozen construction changes Xvfb socket isolation to a private tmpfs mounted inside an unprivileged user+mount namespace. A02 is not retried or relabeled.
