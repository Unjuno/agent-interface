# Source-first freeze — XKB native German round-trip v1

Task `XKB-NATIVE-DE-ROUNDTRIP-20260916-001`, Issue #412.
Immutable base `f224cc42c083c9139185e3f89800fcd21bbea0a4`.
No formal layout application or task input has occurred at this freeze.

Construction was limited to executable availability and confirmation that fresh Xvfb advertises XKEYBOARD. The German resolved definition was compiled offline, without applying it to the server; SHA-256 is `3d3133ea34205324545de76b99d9f65e450d45451a705443336f71a5ac6a7ffd`.

Formal command is exactly `setxkbmap -layout de`; no alternative application command or option may be tried after the first formal outcome. Three fresh `xvfb-run` servers only. Each case dumps baseline server XKB and client core/modifier maps, applies the command once, then dumps them again. No XTEST/key/button event is permitted.

Decision is `PASS_NATIVE_XKB_ROUNDTRIP_PREREQ` only if all three post-server states expose the frozen direct-symbol set and server/core/modifier evidence all change. If sources/audit are intact but that condition is absent, retain `SETUP_BLOCKED_NATIVE_XKB_APPLY`.
