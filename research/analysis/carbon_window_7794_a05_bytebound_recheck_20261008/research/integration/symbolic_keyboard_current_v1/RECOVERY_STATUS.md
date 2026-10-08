# Recovery status (2026-10-01)

The original branch carried `SOURCE_FREEZE.json` and a compact source archive,
not the extracted source tree or formal result package. The archive SHA-256
matches its declaration. Its nine members were extracted byte-for-byte and all
nine SHA-256 entries in `FREEZE.json` verify.

The retained freeze and Issue comment report formal 0/36. No GUI/XKB formal
case was run during recovery. Validation is limited to a read-only,
network-disabled Python 3.13.5 container: source syntax 5/5 and policy unit
tests 8/8 passed. These tests do not validate the X server, layout switch,
application effects, or any formal hypothesis.

The only available local XKB/Xvfb container uses CPython 3.12.3, not the frozen
CPython 3.13.5 environment. The exact required combination is unavailable, so
the formal allocation remains STOPPED at 0/36; the source and gates were not
changed to fit the available image. This is an environment STOP, not a
scientific FAIL or PASS.

This is a source-preservation delivery only. Do not promote runtime behavior
or claim a formal result from policy tests. Issue #4450 and the global ROADMAP
remain open.
