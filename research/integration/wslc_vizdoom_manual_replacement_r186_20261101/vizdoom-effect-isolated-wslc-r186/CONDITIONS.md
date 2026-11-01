# r186: manual isolated-display replacement with fresh game effect

Pre-run: one fresh WSLc allocation, no retry, no model calls. PR #9814 source
head `414a8e95b56c644802232d2f0be3e2cedc0ad92b` with the eight-line
idempotent/logging fixture overlay used by r185. The read-only source manifest
is `../vizdoom-current-owned-target-wslc-r185/source-manifest.json`, SHA-256
`d81b51e2498fb87da67bbe7ce642304ef47abf432dbef4f40936b5b54dba8dfe`.
The unchanged R46 runner SHA-256 is
`254811d7031c1d0b0004d5f98b6bdd5f43f8cadac9f51ae0b7c24ed7ed60c8c3`.
Image `agent-interface-calc-ocr:20261030-a02` ID `6150a4f3c779`, CPU 1,
memory 1 GiB, network none, no pull, source/runner read-only, isolated writable
output, internal 35s watchdog and external 45s timeout.

One forced ordering: old pidfd-owned ViZDoom receives guarded `w`, test queues
one 8s delayed `b`, pauses its authenticated private Xvfb, cancels, retires the
old target and manually kills the display. A new Xvfb reuses the display number
with a new cookie. An XRecord observer covers the old delay horizon; an old
cookie must fail. A fresh DoomGame-managed target uses a fresh MCP owner: compare
600 ms coast (<1 map unit) with W movement (>5 map units); require W press and
release, an explicit later B positive control and no B press before the horizon.

PASS requires all 18 runner gates, one logged delayed injection, zero exit,
unchanged source and clean container completion. Any missing marker, timeout,
skip or failed gate remains FAIL/UNCERTAIN with raw preserved; no re-run with
this ID. Display replacement and fresh target creation are manual test
orchestration; the fresh target is not pidfd-owned. This is a single fixed-order
synthetic case, not automatic recovery, speed, physical desktop, general
reliability, old-task success or MAP01 completion.
