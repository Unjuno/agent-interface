# Fake X release-order counterexample A01

## Result

Decision: `COUNTEREXAMPLE_SEPARATE_UP_FALSE_CLEAR` in normal and optimized
Python 3.11. Both independent-release schedules returned a verified-empty
readback while the original writer was still active; after that writer resumed,
its late `KeyPress` left keycode 37 down while the local held ledger was empty.
The two schedules covered a writer blocked before queueing the DOWN and a DOWN
queued before server processing. The same-connection control did not return
cleanup while its sync was blocked, then applied DOWN followed by UP after
resume. A server-wide processing stop likewise returned no early release
receipt and cleaned up only after resume.

This falsifies the modeled claim that a second connection's UP plus its own
empty readback alone proves bounded release. It supports keeping the outcome
unknown until the original writer is retired/fenced and no later DOWN can be
accepted. It does not establish which cross-connection ordering a real X server
provides, nor does it test production use of a second connection.

## Frozen inputs and retained outcomes

- Base main: `b04f894a06e0f2f6e0a18e2ee636af83c001900c`.
- Final source freeze: `SOURCE_FREEZE.json`, SHA-256
  `15016842f058edb270fa9860a2096925a1a4f3e08a44a6eeec52cff6d32c1cc4`.
- Initial auditor freeze retained as `SOURCE_FREEZE_INITIAL.json`; the
  pre-collection `-O` failure and correction are described in
  `CONSTRUCTION_LOG.md`.
- Normal raw: `raw-normal.json`, SHA-256
  `ab59e7509900fd2729ded68dee0a0e23921e75ff590c9cd254d88dbf46c21fd3`.
- Optimized raw: `raw-optimized.json`, SHA-256
  `9acc37ba74ce1576abec46f215a83345b29774b2ec8b44ac54284a656d77f14b`.
- Independent saved-row audits in both modes returned five cases and two
  false-clear counterexamples. Auditor mutation tests passed 4/4 normal and
  4/4 with `-O`; source-freeze hashes were rechecked after collection.

## Scope and next step

The server is a deterministic synthetic per-connection queue model. Its
five-second barriers are harness escape limits, not measured release deadlines.
No live display, OS input, WSLc, Docker, GUI/MCP caller, MAP01, task effect,
recovery, latency, or efficiency was exercised. This result does not change the
production backend or qualify physical input release. The next meaningful test
must prove that a single authority can retire/fence the original writer and
reject late input while preserving a separately evidenced physical release;
if that cannot complete under backend/server stall, report `UNKNOWN` rather
than a finite guarantee.
