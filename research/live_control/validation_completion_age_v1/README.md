# Validation-completion age (#4010)

Premeasurement source freeze for one 21-case private-X11 read-only allocation.
See PLAN.md and FREEZE.json. No formal result is claimed by this commit.
All files are additive research scope; no shared runtime is promoted.

The unchanged native acquisition source is native.c. The exact locally compiled
Linux x86_64 helper is retained losslessly as native.so.xz (compressed SHA256
3d3178710bbfe17f05b9f00ec22ce49da6e649306655868566e3510206b5b155).
For audit-only source checking, decompress it to native.so and compare its
SHA256 to FREEZE.json; the audit does not load or execute this library.
Do not execute it on an incompatible ABI or rerun a consumed allocation.

The legacy FRAME_FRESH label means fresh at receipt. The candidate additionally
records freshness at a post-validation clock sample, never action authority,
semantic currentness, or a promise about later model use. Verification delay is
explicitly injected, not a measured normal hash cost or causal GIL mechanism.

Construction failures and the old 13/32 HOLD are retained locally and will be
reported separately; construction/raw-result publication is not yet complete.
The earlier complete archive remains a conversation attachment, not claimed
hosted here. Parents #2117/#2789 and the broad ROADMAP remain open.
