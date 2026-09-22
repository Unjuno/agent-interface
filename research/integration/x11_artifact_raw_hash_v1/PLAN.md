# PLAN — X11 artifact raw-hash injectivity

Issue #4106. Prospective public freeze before formal execution.

## H
For each supported byte order, changing only the ignored X byte of one accepted 32-bit pixel changes SHA256(raw) but leaves the RGB PNG byte-identical. Changing one visible channel must change decoded RGB and PNG bytes.

## T
Exact production `CaptureArtifacts.write` blob `d20d67bc06d92d99859681f62fbeb9c2f13aab70`.
Six fresh subprocesses: BGRX base/X-only/visible-change and XRGB base/X-only/visible-change. width=height=1, depth=24, bpp=32, scanline_pad=32, masks=(0xff0000,0x00ff00,0x0000ff), TrueColor. No X server/input/model/network.

## D
PASS_RAW_HASH_NONRECONSTRUCTIBLE_FROM_PNG_SCOPED iff for both byte orders: base and X-only raw hashes differ; exact PNG bytes/hash and decoded RGB match; visible-change decoded RGB and PNG differ; every returned source_raw_sha256 equals submitted raw SHA256; all six exits are 0; independent stdlib PNG audit and corruption controls pass. Complete contradiction is FAIL; dependency/source/process/evidence ambiguity is HOLD/STOP.

## C
This validates the exact encoder mapping, not empirical X-server padding distributions. A trusted producer may report source_raw_sha256 correctly even though artifact-only consumers cannot derive it.

## U
No live X11 capture, authentication/currentness, concurrency, model/task utility, performance/token benefit, or production promotion.

## Variables / units
| symbol/field | meaning | SI unit | definition | domain | type |
|---|---|---|---|---|---|
| raw | submitted X11-format pixel bytes | byte (information, not SI) | one 4-byte pixel | length 4 | byte string |
| X | ignored/padding byte in BGRX/XRGB conversion | byte | raw position ignored by RGB conversion | 0..255 | integer |
| RGB | decoded visible pixel | dimensionless channel code | PNG decoded color | each 0..255 | 3-vector integer |
| H_raw | SHA-256 of raw | dimensionless | SHA256(raw) | 256-bit | byte/string digest |
| H_png | SHA-256 of PNG | dimensionless | SHA256(PNG bytes) | 256-bit | byte/string digest |

Dimensional check: only byte equality/digest equality is used; no physical-time quantity enters the decision.
