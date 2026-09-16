# Research Preview support envelope

## RC1 supported target

| Platform / backend | RC1 status |
|---|---|
| WSLg + Linux/X11 + Chromium + Windows Codex CLI bridge | Preview target; requires supported-host acceptance |
| Generic Linux/X11 | Not claimed; prerequisites may work but are not the RC1 support promise |
| Native Windows | Not yet supported by the promoted runtime path |
| Native macOS | Not yet supported by the promoted runtime path |
| Wayland-native | Not yet supported |

## Required external pieces

- Python 3 environment capable of installing the pinned `runtime/requirements-golden.txt` set
- WSLg/X11 display connectivity
- Chromium / Google Chrome as documented by the runtime doctor
- Windows Node.js and Codex CLI bridge paths visible from WSL

## Release semantics

This preview promotes a narrow retained desktop path. Research branches may contain newer mechanisms; they are not automatically part of the release. The RC does not move when `main` moves.

## Failure policy

A setup, doctor, retained-audit, fresh-run, or live-audit failure is release evidence. Do not bypass a failed gate by widening claims, changing benchmark thresholds, or substituting a generic container for the supported host.

## Cross-platform roadmap

The intended architecture keeps OS-specific observation/input/focus/permission work behind backend adapters while shared binding, authority, execution-receipt, outcome, and recovery contracts remain platform-neutral. Native Windows and macOS backends are post-preview work and require their own correctness evidence before support is claimed.
