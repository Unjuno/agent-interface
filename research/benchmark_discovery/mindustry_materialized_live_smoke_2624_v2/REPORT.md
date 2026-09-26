# Issue #2624 — Mindustry materialized live-smoke retained outcomes

## Result

Two distinct prospectively frozen allocations are retained. The first is not rewritten.

- V1 `mindustry-materialized-live-smoke-2624-20260922-01`: `FAIL_ORACLE_MISMATCH`. All fixture/readiness/window/zero-call/cleanup gates passed, but its frozen scorer expected width=300,height=250. The raw oracle was width=250,height=300.
- Read-only post-result provenance showed V1's raw `oracle.json` has Git blob `fb7cd0e88e730401b32c2954b58c8c02ec83fcc6`, exactly the same blob already retained on main for historical create/reload-1/reload-2 canonical reset evidence. This isolates a scorer-orientation mistake rather than a changed fixture.
- V2 `mindustry-materialized-live-smoke-2624-20260926-02`: `PASS_MINDUSTRY_MATERIALIZED_LIVE_SMOKE_SCOPED`. It changed only the prospectively frozen scorer orientation/reference contract. Ready occurred in 5.852 s; the exact historical oracle blob and decoded fields matched; a Mindustry window existed; task/controller/model/provider calls were all zero; Mindustry/Openbox/Xvfb all terminated without SIGKILL; independent audit returned no errors; 8/8 evidence corruptions were rejected.

## H/T/D/C/U

**H.** The exact pinned fixture satisfies the intended historical canonical-projection gate when scoring is bound to the pre-existing oracle identity rather than V1's transposed interpretation.

**T.** One fresh V2 private Xvfb/Openbox/Java21 session, 60 s timeout, exact same four fixture members, zero task/controller/model/provider calls, no retries/replacements/tuning.

**D.** PASS requires exact fixture identities, readiness, byte-identical historical oracle, correct decoded dimensions/scalars, top-level Mindustry window, zero call counters, cleanup, independent audit and corruption controls.

**C.** The historical oracle blob predates V1/V2, so V2 does not select a favorable oracle after seeing V2. V1 remains FAIL.

**U.** This is setup-only one-session evidence. It does not establish repeat-reset reliability, task/controller correctness, gameplay, model economics, token/latency benefit, human tempo, or product readiness. It only removes the exact-asset zero-input live-start gate for #1679/#57.

## Acquisition chronology

The 2026-09-22 setup artifact expired. On 2026-09-26 only the already-successful setup acquisition job was rerun. The regenerated ZIP container has a different packaging digest, but all four scientific fixture members were independently rehashed and exactly match the frozen identities. No scientific formal run occurred during acquisition.

## Publication limitation

The dedicated branch was created from current main and the V2 metadata/auditor files that had completed before the safety boundary have exact Git-blob readback matching local bytes. The first repository write containing `run.py` was blocked by the connected tool's safety check. That blocked write was not bypassed. Therefore this evidence bundle contains complete raw outcomes and source identities but **not the V2 runner source bytes**. Scientific disposition and source-publication/review disposition are intentionally separate. Do not promote this PASS into a merged integration claim until exact runner bytes are reviewable.
