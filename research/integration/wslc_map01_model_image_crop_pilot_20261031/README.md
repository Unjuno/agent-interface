# Static MAP01 screenshot crop: model-call pilot

This exploratory offline replay compares a full 1280×1024 X11 screenshot with the exact 640×480 game-window crop from the same pixels. The two retained synthetic MAP01 images come from the fifth-decision and bounded-retry studies: one has a visible central hostile and one has no visible hostile in the inspected view. Each image is shown twice per arm in the frozen order shown below, using a fresh independent `gpt-6.1-sol` low app-server session per call. The same prompt asks for `fire` and a hostile center in supplied-image coordinates, or `idle` with zero coordinates. No live game, input, guard, cancellation or task effect is exercised.

| Run | Scene | Image | Coarse score | Model-call interval (s) | Input tokens | Cached input subset | Output tokens |
|---|---|---|---|---:|---:|---:|---:|
| a01 | hostile visible | full | pass | 6.828 | 12,431 | 0 | 63 |
| a02 | hostile visible | crop | pass | 4.476 | 11,256 | 0 | 65 |
| a03 | hostile visible | crop | pass | 5.366 | 11,256 | 8,192 | 66 |
| a04 | hostile visible | full | pass | 6.169 | 12,431 | 0 | 65 |
| a05 | no hostile visible | crop | pass | 3.809 | 11,256 | 8,192 | 30 |
| a06 | no hostile visible | full | pass | 4.555 | 12,431 | 0 | 30 |
| a07 | no hostile visible | full | pass | 3.527 | 12,431 | 0 | 30 |
| a08 | no hostile visible | crop | pass | 3.154 | 11,256 | 8,192 | 30 |

For this pilot, the positive score requires `fire`, a 500 ms proposal and a center inside the predeclared, manually inspected full-screen box `[625,440,715,592]`; crop coordinates are translated by `(320,272)` before scoring. The negative score requires `idle`, zero coordinates and zero duration. All eight responses passed this coarse criterion. It is not an independent semantic oracle, a hit test or a claim that the proposed action is appropriate in the live game.

The input count was 12,431 for each full image and 11,256 for each crop: 1,175 fewer reported input tokens (about 9.45%) in this fixed prompt/session setup. Median input plus output was 12,477.5 versus 11,303.5 tokens. Cached input is already included in input; it must not be added again. Cost was not supplied. The recorded model-call intervals had medians 5.362 s full and 4.143 s crop, but the sample is tiny, repeated on only two development-selected images, ordered rather than randomized, and three crop calls reported cached input while none of the full calls did. No general speed or price advantage can be inferred. The interval covers adapter turn start through completed response; session startup, teardown, cropping, screenshots, local guard and game effect are excluded.

The crop intentionally removes all pixels outside the known game-window rectangle. It may discard relevant context in other tasks or scenes; a fixed coordinate conversion is unsafe after geometry or display changes. This experiment does not establish target freshness, live correctness, general reliability, MAP01 completion, or that cropping reduces end-to-end time. Broader matched scenes, uncertainty and rejection cases, variable window geometry and live effect/recovery tests are needed.

`pilot.zip` retains frozen conditions, the exact adapter source extracted from main `adcc3dc508eaf2c0b1cd567668d0154595e926e1`, schema, prompt, input PNGs, per-call structured results and usage. The archive also includes a local protocol-check attestation: before packaging, each private app-server journal was checked for exactly one sent `turn/start`, the exact frozen prompt and the expected local image path. The private journals remain local and are represented by paths, byte counts and SHA-256 in `private-local-manifest.json`; the public auditor cannot independently re-read those private bytes or prove provider execution. `python audit.py` (Pillow, normal mode) verifies frozen hashes, full/crop pixel identity against the two retained source archives, independent session/call IDs, response/usage linkage, coordinate scoring and medians. All sessions recorded closure; no extra model call is made by the audit.
