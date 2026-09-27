# Current-path compatibility review — 2026-09-22

This is a post-experiment read-only source inspection, not a new live test.
GitHub MCP returned `runtime/backends/x11_v1/backend.py` at intake main
`e4c2e58122aa138e421048d8e86ec18259143b9e`, Git blob
`9cae101a219348077668c8fc086acf8e13154afe`, lines 250–353.

`release_all()` copies tracked keycodes, emits their releases and held-button
releases, synchronizes the X connection, clears owner bookkeeping, and queries
`_physical_keys_down(tracked)` plus `_physical_buttons_down()`. It returns
`verified: not keys and not buttons` with a monotonic sample. The key helper calls
`query_keymap`; the button helper calls `root.query_pointer`. This path does not
count received KeyRelease events as proof of neutrality.

Consequently, #4041 does not demonstrate a release-event-count bug in this backend
and supplies no reason to replace its existing sampled-state check. The source
uses the word physical, but these API observations are server logical samples;
they do not certify hardware, continuous neutrality or no previous application
effect. The inspected key helper checks tracked keys, not a complete hardware
inventory. No stronger coverage or concurrency guarantee is inferred here.

Integration decision for #57/#2789: preserve the existing sampled-state boundary;
keep any future event-driven telemetry explicitly non-authoritative and record
its per-connection negotiation. Score application text/effects independently.
Actual public CLI/admission integration, post-sample interference, other keys and
applications, model judgment and matched benefit are untested by #4041. No shared
runtime source, default or production acceptance gate is changed.
