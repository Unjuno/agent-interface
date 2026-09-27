# XGetImage String8 normalization — scoped boundary experiment

Issue: #4455, successor to the stopped #4304 allocation. Preserve #4304 and all predecessor evidence unchanged.

## H — hypothesis

In the recorded Python-Xlib stack, `XGetImage` payloads exposed as `str` make the shared backend's `bytes(image.data)` raise `TypeError`. Encoding that `str` back with UTF-8, while preserving already-byte payloads unchanged, will recover the exact native XImage payload for every frozen case without changing length, geometry, or byte hash.

This is a representation-boundary and source-preservation result only; it is not general X11, semantic image, model, latency, or production-reliability evidence.

## T — formal treatment

- Environment: existing local Docker Desktop image `agent-interface-mcp-live:retention-01` (linux/amd64, Python 3.12.14, Python-Xlib 0.33). Exact image digest and supporting package versions will be frozen in `ENVIRONMENT.json`. This is not the Python-Xlib 0.15 stack discussed in the issue's prior construction note; conclusions apply only to this available 0.33 stack. No network, package installation, model/provider, GUI desktop, or user data.
- Each case starts a fresh TCP-disabled, cookie-authenticated Xvfb server and a fresh fixture process. The fixture paints one deterministic 8x8 byte-pattern into either the root drawable or a child window. A separate native libX11 connection calls `XGetImage` as the byte oracle.
- Five frozen patterns: all-zero; low-ASCII/UTF-8-decodable; a valid multi-byte UTF-8 sequence; high-byte/non-UTF-8; mixed pattern. Two drawables (root and child window), three repetitions each: 30 cases, fixed order in `SCHEDULE.json`.
- Record Python-Xlib payload type, legacy `bytes(image.data)` outcome, UTF-8/bytes candidate result, native raw payload, geometry/depth/stride, hashes, process IDs/exits, and cleanup. The only proposed runtime expression is `image.data.encode("UTF-8") if isinstance(image.data, str) else bytes(image.data)`.

## D — frozen gates

`PASS_X11_STRING8_NORMALIZATION_BOUNDARY_SCOPED` requires all 30 cases and process receipts to reconcile; at least one legal `str` payload for which the legacy conversion raises; exact candidate/native byte equality for every `str` and `bytes` case; unchanged existing byte payloads; zero length/hash mismatches; an independent raw-only auditor with zero errors; and at least eight effective evidence-corruption controls rejected. A fully audited run with no `str` is a valid environment-specific HOLD, not evidence that Python-Xlib 0.15 behaves the same.

No runtime patch is permitted unless every gate passes. If no live string payload is exposed, retain `HOLD_NO_LIVE_STRING8_DISCRIMINATOR`; any normalized-byte mismatch is FAIL; missing source/process/raw evidence is HOLD/STOP. No case replacement, retry, exclusion, or post-result tuning.

## C — competing explanations

UTF-8 reversal is justified only by the installed Python-Xlib String8 decoder contract and must be tested with a valid multi-byte sequence as well as invalid high bytes. The available 0.33 `GetImage` path uses `rq.Binary('data')`; it may therefore expose only `bytes`, unlike the historical 0.15 behavior described in the issue. Server format, pixel layout, or drawable differences may explain individual representations; the native oracle distinguishes conversion correctness from Python-Xlib decoding.

## U — residual uncertainty

This does not establish the historical Python-Xlib 0.15 behavior, pixel-channel/endian interpretation, image freshness, semantic meaning, model utility, latency, application effect, non-X11 backend behavior, or production reliability. The fixture uses deterministic synthetic drawables only. Any 0.33 HOLD leaves the 0.15 question unresolved and does not authorize a runtime patch.
