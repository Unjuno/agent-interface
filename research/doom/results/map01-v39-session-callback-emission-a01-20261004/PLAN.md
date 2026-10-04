# v39 session callback emission construction A01

Status: construction-only. This package checks one integration boundary needed before any new live allocation.

- **H:** The exact `session_map01_v12.main()` callback path on PR #7355 head `531db11bff3b8822cc980023e75bcd3890de7257` preserves an `input_release_transition` row, its nested owner-thread key-up receipt, and `owner-events` through the actual backend-to-logger callback and cleanup serialization.
- **T:** Invoke the exact session `main()` source with a fake VizDoom game, fake X11/session, fake Executor, and deterministic owner. Submit one `W` down/up program, then finish. Retain stdout, `events.jsonl`, `delivered.jsonl`, `owner-events.json`, source identities, and an auditor result.
- **D:** PASS only if exactly one release transition and one explicit owner-key-up record are retained; the nested receipt identity/timestamps and batch identifier survive; `events.jsonl` and `delivered.jsonl` are byte-identical; owner release is verified empty; all pinned source hashes match. Any missing or altered field is FAIL.
- **C:** Every environment boundary is stubbed. This tests the session callback and serialization integration, not X server scheduling, physical input, game feedback, or task effect. Existing C02 already exercises the v10 owner on Xvfb; this is a distinct session-output boundary.
- **U:** One deterministic synthetic session, no physical input, no live game/model, no latency or recovery measurement, no formal allocation. The initial A01 execution passed but wrote outputs under a temporary directory; its retained summary has no raw logs. The captured run below is a reproducibility capture, not an independent replication or formal allocation.
