# #2699 Xauthority identity successor result

Date: 2026-09-20

Decision: `FAIL_XAUTH_COOKIE_IDENTITY`

This additive run preserved the original #2699 source and added only the
missing `xauth` executable identified by the prior dependency stop.

## Provenance

- Base image: `mixed-app-2794:local`
- Base image digest: `sha256:62ccc9b512e8b9cd0c5dc7b9778c08617d124df85f83738b9bfe21a4e28123b2`
- Added package: Debian `xauth 1:1.1.2-1`
- Runtime: local Docker, `--network none`, read-only source, tmpfs runtime
- Runner: `research/integration/mixed_app_long_session_2499_xauth_v1/xauth_identity.py`

## Result

The runner reached identity resolution. Calc produced exactly one candidate,
but its validated properties identified `LibreOffice 7.4 - Fatal Error`, not a
healthy Calc surface. Inkscape and Chromium produced zero candidates. The
missing-token control produced zero candidates and refused safely. Input,
model, and network counters were all zero. Xauthority mode was `0600`.

This is a genuine identity/startup failure after dependency repair, not an
infrastructure stop. It does not qualify #2499 or rewrite #2664/#2499 history.
The next experiment must diagnose Xauthority/Xvfb propagation and application
startup before any integrated-session allocation.
