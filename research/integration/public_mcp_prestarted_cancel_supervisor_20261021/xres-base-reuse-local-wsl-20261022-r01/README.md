# XRes resource-base reuse diagnostic — stopped before probe

**Disposition: `STOP_ENV_BEFORE_XVFB`.** This packet records a failed
environment preflight, not an XRes result. No owner, replacement, observer,
XRes query, or input event ran.

The run used the corrected `probe.py` in ordinary Ubuntu WSL, Python 3.12.3,
python-xlib 0.33, and the installed Xvfb. Both private Xvfb displays were
requested with `-nolisten tcp`. Xvfb could not create its Unix listener because
`/tmp/.X11-unix` had mode `0777`; the server reported that it expected `01777`
and exited before display `:89` became ready. The runner stopped before the
probe and did not change shared `/tmp` permissions or enable TCP listening.

The diagnostic code had been corrected to pass the owner request over a pipe
to a helper process that was started before the owner. That construction was
not exercised. Do not infer whether the observer or an unrelated client
received the retired owner's resource base. Reattempt only after an isolated
local Xvfb socket path can be provided without changing shared host settings.
This is not WSLc evidence and grants no allocation.

## Retained files

- `probe.py`: corrected, not executed.
- `run-probe.sh`: runner; startup failed at the Xvfb readiness check.
- `xvfb-89.log`, `xvfb-90.log`: raw Xvfb startup logs.
- `probe.stdout.log`, `probe.stderr.log`, `exit_code.txt`: runner outcome.
- `conditions.txt`: host, source, and input-event scope.
- `runtime.patch.txt`: exact uncommitted runtime changes present during the
  attempted preflight; not part of the probe's result.
- `SHA256SUMS`: hashes of the retained source, conditions, and raw artifacts.

The earlier Xvfb run remains the only relevant observed supervisor outcome:
XRes found a different PID at the retired owner's resource base, so the caller
failed closed as `resource_base_reused`; input release and task effect remained
unknown/unreached. This stopped preflight neither revises nor extends that
result.
