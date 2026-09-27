# Executed runner publication integrity repair v1

Status: **PUBLICATION REPRODUCIBILITY REPAIRED; EXPERIMENTAL RESULT UNCHANGED.**

The formal container/X11 v3 result was produced from `/tmp/container_x11_bounded_recovery_v3.py` before `summary.json` was written. A post-publication reproducibility check then found that the first GitHub copy of `research/container_control/container_x11_bounded_recovery_v3.py` was not byte-identical to that executed file.

## Detected mismatch

Executed container file:

- size: **18,920 bytes**;
- SHA-256: `91651acb1ff1c1d9ce3478738bcc9eb7108fed95693a5c8d1427d31c0ee68a53`;
- Git blob SHA-1 recomputed locally: `a6bcd33f116e75273f44392d9bb6f6f0e69d70ee`;
- filesystem mtime: `2026-09-15 12:18:02.454421393 +0000`.

First published GitHub copy:

- size: **18,238 bytes**;
- Git blob SHA-1: `f3bf2e19698397fde62d904f8f7df934df674a2a`.

Formal result summary:

- filesystem mtime: `2026-09-15 12:18:27.350604619 +0000`;
- therefore the retained 18,920-byte local runner predates and is the runner used by the formal v3 execution.

The mismatch was found before starting the held-out transfer allocation. That allocation was stopped rather than using a dependency whose published bytes differed from the executed provenance.

## Repair

The branch copy was replaced with the exact 18,920-byte executed runner. GitHub returned content blob:

`a6bcd33f116e75273f44392d9bb6f6f0e69d70ee`

which is identical to the Git blob SHA-1 independently recomputed from the executed local bytes.

No `summary.json`, raw event stream, threshold, task dynamics, metric, or scientific disposition was changed by this repair. The raw first-result evidence remains independently hash-bound by `raw-manifest.json` and reconstructs to SHA-256 `9037fe0f3393e8cefa50225362ee2caec661a34dc64381cdaabd0b4fd2194cd3`.

## Disposition

- v3 mechanics result: unchanged;
- first GitHub runner publication: **rejected as non-reproducible copy**;
- repaired GitHub runner: **byte-identical to executed file**;
- downstream formal transfer work: may proceed only from a branch containing blob `a6bcd33f...` and a separately frozen preregistration.

This check is retained because successful source publication is not itself evidence that the published source matches the executed source.