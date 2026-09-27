# Formal result — XGetImage String8 normalization (#4455)

## Decision

`HOLD_NO_LIVE_STRING8_DISCRIMINATOR` for the available Docker image only. Do not modify the shared X11 runtime. The issue's historical Python-Xlib 0.15 behavior remains unresolved; this run used Python-Xlib 0.33.

## Frozen run

One frozen formal invocation completed 30/30 scheduled cases with zero failed cases. All 30 `image.data` values were `bytes`; zero were `str`, and therefore zero legacy `bytes(image.data)` TypeErrors were observed. Candidate/native byte mismatches: 0. Source-pixel/native-oracle mismatches: 0. Raw JSONL SHA256: `dd018575f26d6e365877216ebd0021ec6578c636a09fc4503656d59c737a58cf`.

Environment: Docker Desktop Engine 28.5.1; image `sha256:f82bbd2c087056f324794ca9b0de64c16f0ecaf9a84f30bb0aba17b5b1833786` (`linux/amd64`); Python 3.12.14; Python-Xlib 0.33; Tk 8.6; Xvfb 2:21.1.16-1.3+deb13u4; xauth 1:1.1.2-1.1; libX11 2:1.8.12-1. Packages and source hashes are in `ENVIRONMENT.json` and `FREEZE.json`.

## Independent verification

The raw-only auditor accepted all 30 rows with 18 checks and zero errors; its decision is HOLD for zero live string payloads. Twelve deliberate copied-evidence corruptions were all rejected (12/12). Unit tests: 5/5 passed before the formal allocation. Construction failures and excluded successful construction probes remain preserved under `construction/` and are not counted as formal cases.

## Scope

This neither disproves the issue's Python-Xlib 0.15 observation nor validates UTF-8 normalization for a live `str` payload. The historical 0.15 environment remains a prerequisite for resolving the original discriminator. This run provides no basis for a runtime patch or production claim.
