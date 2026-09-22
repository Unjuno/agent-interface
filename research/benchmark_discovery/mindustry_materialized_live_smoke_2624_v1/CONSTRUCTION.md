# Construction history

- construction-01: setup-only Xvfb/Openbox check failed before any Mindustry/Java
  launch because the local Openbox build does not accept `--display`. Xvfb was
  cleaned up after diagnosis. This is excluded construction, not formal evidence.
- correction before freeze: pass `DISPLAY` only through the environment and use
  `openbox --sm-disable`. No scientific gate, asset, timeout, application action,
  or formal denominator changed.
- construction-02: corrected DISPLAY-via-environment Xvfb/Openbox lifecycle
  passed readiness/liveness and cleanup checks without launching Java/Mindustry.
  Openbox returned 1 after requested SIGTERM; no SIGKILL was used. Xvfb returned 0.
- local manifest helper incident: an initial `sha256sum *` command exited 1 only
  because `__pycache__/` was a directory. File bytes were then hashed explicitly;
  no study source was changed by that incident.
