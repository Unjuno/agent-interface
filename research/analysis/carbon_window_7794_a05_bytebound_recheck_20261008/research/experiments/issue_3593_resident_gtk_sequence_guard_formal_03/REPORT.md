# Issue #3593 — GTK visible-effect formal allocation 03

## Decision

`PASS_INDEPENDENT_GTK_SEQUENCE_GUARD_AUDIT` for the finite synthetic GTK/Xvfb schedule only. The guarded candidate refused the delayed replacement rollback path that caused the upstream candidate to emit an action. This is not evidence of production Agent Interface integration, public X11 event-source causality, broad GUI reliability, latency benefit, or human-tempo improvement.

## Preregistered design and execution

- Allocation: `issue3588-resident-gtk-sequence-guard-formal-03`, Issue #3593.
- Image: `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, `linux/arm64`.
- 9 exact construction traces × 2 actual policy candidates × effect on/off = 36 rows; 108 event prefixes.
- Each candidate's `step` consumed one event at a time. Every emitted action generated an immediate XTest Space press/release before the next event.
- Network disabled; source read-only; fresh evidence mount writable. One formal invocation, zero retries.
- Formal runner reported 36 rows, zero row errors, all key releases, and all process/socket cleanup.
- Independent audit separately replayed prefixes and checked visible titles, image bytes/hashes/dimensions, process incarnation/reap, and source/freeze linkage. Audit errors: zero. Four corruption challenges detected 4/4.

## Key result

| Trace / policy | Effect enabled | Effect disabled |
|---|---:|---:|
| Delayed replacement rollback — upstream | 1 emitted action; GTK title `resident-fixture:1` | 1 emitted action; GTK task effect 0 |
| Delayed replacement rollback — sequence guarded | 0 emitted actions; GTK title `resident-fixture:0` | 0 emitted actions; GTK task effect 0 |
| Current rising edges — each policy | 2 actions / 2 visible effects | 2 actions / 0 visible effects |
| Valid new generation — each policy | 1 action / 1 visible effect | 1 action / 0 visible effects |

All 36 rows retained before/after 153,600-byte raw GTK-window frames (320×120×4), SHA-256 hashes, and per-prefix title/effect counts. Each emitted press was followed by a verified key-up read before the next event. All 72 Xvfb/fixture process instances were reaped and their X sockets disappeared.

## Immutable predecessor STOPs

- Formal-01 never invoked the runner: frozen fixture path disagreed with the source layout; zero rows.
- Formal-02 invoked the runner once but stopped before any GTK row because Python could not resolve sibling policy modules; zero rows.
- Their STOP records remain at their original paths in the experiment branch. Formal-03 changes only startup path handling and allocation identity; trace schedule and acceptance gates are unchanged.

## Reproduction evidence and hashes

- Raw result SHA-256: `6bb4cead96e12da691f6aa2ee112a517e33b27ef462b7d20daf9e49631246f8e`.
- Independent audit SHA-256: `2fef36d48088277d3fc7a3bb5bfd5a3b6a0c9c56214c51ebc9a41bd10802d280`.
- Compressed raw frame bundle SHA-256: `6d8bb35b1479ce18ac63f3987680f9e3e4e0cac6aa36cd2a959138b83bd073ee`.
- Freeze SHA-256: `9a99b29ed1f148ea416b8296de72361bcf1cc63f2bc1fa7ed54e6859a7ecd882`.
- Source manifest SHA-256: `d46a0954c808bda786a2e19751c421f0e0e93c70be25558374f7def43aaaf20c`.
- Upstream source is the unchanged main-branch blob `37bb7b271b099ccb10a594dbe00faa5bf618099b`; guarded source is the construction-tested candidate retained from PR #3591.

See `FREEZE.json`, `SOURCE_MANIFEST.json`, `src/`, `raw.json`, `audit.json`, and `frames/` in `research/experiments/issue_3593_resident_gtk_sequence_guard_formal_03/`.
