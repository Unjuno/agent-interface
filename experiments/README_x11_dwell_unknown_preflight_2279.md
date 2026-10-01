# X11 dwell UNKNOWN preflight (#2279)

Research-only Xvfb/Tk fixture for the dwell-time successor experiment.

It deliberately distinguishes:

- COMPLETED: the delayed GUI fixture effect is observed before the horizon
- UNKNOWN: the effect is absent or arrives after the observation horizon

Each case creates and destroys its own Tk root. This prevents delayed callbacks from leaking into the next case; that leak was detected and discarded during the initial local run.

## Scope

This is a container preflight, not production live-GUI evidence. It does not establish the #2279 acceptance criteria, validate a real task effect, or change runtime timeout policy.

## Run

Use the existing X11 preflight image:

```bash
Xvfb :99 -screen 0 1024x768x24 &
DISPLAY=:99 python experiments/x11_dwell_unknown_preflight_2279.py
```
