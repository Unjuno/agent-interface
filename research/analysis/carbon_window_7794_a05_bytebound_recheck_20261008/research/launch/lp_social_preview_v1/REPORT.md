# LP social preview — retained publication-integrity block

Task `LP-SOCIAL-PREVIEW-20260916-001`, Issue #549.

## Decision

**`BLOCKED_ASSET_PUBLICATION_INTEGRITY`**.

The container-side visual/metadata construction passed, but the candidate was **not** promoted to the landing page because binary publication through the available GitHub connector path did not reproduce the locally verified Git blob identity.

## Construction

A deterministic Chromium-rendered social card was produced locally from static HTML/CSS only.

Initial RGB PNG:
- 1200×630;
- 55,058 bytes;
- SHA-256 `5c4b8715837875aba65cb467ab66bd8d4864f88f181ddd23d68ab46d13e72bef`;
- local Git blob `146672deff45615a7b449d51415cda049beeac7a`.

To reduce transfer risk, palette variants were also generated. The retained 8-colour candidate remained visually legible at 1200×630, 13,467 bytes, SHA-256 `fc477f3fce9449e2063ccbd03d4718aea62b974cc3072444b01549d35497eb30`, local Git blob `fc37a76472af678ccf92bdb4010509a047c99ca1`.

Static candidate metadata passed the frozen completeness checks for `og:image`, dimensions/type/alt, `twitter:card=summary_large_image`, `twitter:image` and alt, with one canonical HTTPS asset and no planned body/layout mutation.

## Publication failure

The first remote binary blob obtained through connector/base64 publication was `af81509c1c481f5f814ff39835e3fe720c7e1d62`, which does not equal the local candidate object identity. A second reduced-size transfer produced remote blob `59558b26976d159e5886b411aa0ce253637be978`, again not equal to the corresponding local object. A direct tree reference to the correct 8-colour local blob `fc37a76472af678ccf92bdb4010509a047c99ca1` was rejected because that object was not present remotely.

The incorrectly uploaded `site/og-image.png` was removed from the branch. `site/index.html` was not changed.

## Interpretation

The visual card and static metadata design remain viable construction artifacts, but **asset publication integrity is a prerequisite**. It is better to retain a blocked result than publish an image whose bytes cannot be tied to the measured candidate.

This is an infrastructure/publication boundary, not evidence against Open Graph metadata itself.

## Next condition

Resume only when a binary upload path can prove remote Git blob equality with the local candidate (for example a normal Git push or a connector action with a true file parameter). Then re-run the frozen metadata checks against the exact retained asset before landing-page mutation.

## Limits

No live OpenGraph/Twitter/Slack/Discord/Product Hunt scraper, cache behavior, CTR, conversion or page-load endpoint was measured.

## ERROR CHECK

- local dimensions: 1200×630 — PASS;
- candidate size <500 KB — PASS;
- static metadata completeness — PASS;
- remote/local Git blob equality — **FAIL**;
- wrong remote asset retained in site tree — NO;
- `site/index.html` mutated by this experiment — NO.
